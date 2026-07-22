import httpx
import re
from urllib.parse import unquote
from user_scanner.core.result import Result


async def _check(user: str) -> Result:
    base_url = "https://chaturbate.com"
    show_url = f"{base_url}/{user}/"
    register_url = f"{base_url}/accounts/register/"
    check_api = f"{base_url}/accounts/ajax_validate_register_form/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
        "Referer": register_url,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    async with httpx.AsyncClient(http2=True, follow_redirects=True, timeout=15.0) as client:
        try:
            landing = await client.get(register_url, headers={"User-Agent": headers["User-Agent"]})
            token_match = re.search(
                r'name="csrfmiddlewaretoken"[^>]*value="([^"]+)"', landing.text
            )

            if not token_match:
                return Result.error("Failed to extract CSRF token from HTML", url=show_url)

            payload = {"csrfmiddlewaretoken": token_match.group(1), "username": user}

            response = await client.post(check_api, data=payload, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited, wait for a few minutes", url=show_url)

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}", url=show_url)

            username_error = response.json().get("errors", {}).get("username", "")

            if "already taken" in username_error:
                extra = await _fetch_biocontext(client, base_url, user, headers["User-Agent"])
                return Result.taken(extra=extra, url=show_url)

            # Other username errors are format rejections (length, characters),
            # not an existence signal.
            if username_error:
                return Result.error(username_error, url=show_url)

            return Result.available(url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_chaturbate(user: str) -> Result:
    return await _check(user)


async def _fetch_biocontext(client: httpx.AsyncClient, base_url: str, user: str, user_agent: str) -> dict:
    """The register check only reports availability. Broadcaster accounts also
    expose a public biocontext JSON; non-broadcaster names 404 here, so this is
    best-effort and yields no extra on failure. A browser User-Agent is required
    or the endpoint serves an HTML challenge page instead of JSON."""
    try:
        api_headers = {"User-Agent": user_agent, "X-Requested-With": "XMLHttpRequest"}
        response = await client.get(f"{base_url}/api/biocontext/{user}/", headers=api_headers)
        if response.status_code != 200 or "json" not in response.headers.get("content-type", ""):
            return {}
        return _extract_biocontext(response.json())
    except Exception:
        return {}


def _extract_biocontext(data: dict) -> dict:
    extra = {}

    if value := data.get("real_name"):
        extra["fullname"] = value
    if value := data.get("location"):
        extra["location"] = value
    if value := data.get("display_age"):
        extra["age"] = str(value)
    if value := data.get("display_birthday"):
        extra["birthday"] = value
    if value := data.get("sex"):
        extra["gender"] = value
    if value := data.get("subgender"):
        extra["subgender"] = value
    if value := data.get("body_type"):
        extra["body_type"] = value
    if value := data.get("follower_count"):
        extra["followers"] = str(value)
    if value := data.get("time_since_last_broadcast"):
        extra["last_broadcast"] = value

    interested = [x for x in (data.get("interested_in") or []) if isinstance(x, str)]
    if interested:
        extra["interested_in"] = ", ".join(interested)

    languages = data.get("languages")
    if isinstance(languages, list):
        languages = ", ".join(x for x in languages if isinstance(x, str))
    if isinstance(languages, str) and languages.strip():
        extra["languages"] = languages.strip()

    about = data.get("about_me") or ""
    if about:
        bio = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", about)).strip()
        if bio:
            extra["bio"] = bio

    links = []
    for social in data.get("social_medias") or []:
        match = re.search(r"url=([^&]+)", social.get("link") or "")
        if match:
            links.append(unquote(match.group(1)))
    if links:
        extra["links"] = ", ".join(dict.fromkeys(links))

    return extra
