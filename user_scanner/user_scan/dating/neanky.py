import html
import re
from urllib.parse import quote, urljoin

import httpx

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result


def validate_neanky(user: str) -> Result:
    username = user.strip()
    url = f"https://neanky.ee/user/{quote(username, safe='')}"

    def process_profile(response: httpx.Response) -> Result:
        if (
            response.status_code == 404
            and "<title>Kasutajat ei leitud | Neanky" in response.text
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        if pending := re.search(
            r"Soovitud kasutaja ei ole hetkel veel aktiveeritud!<br>\s*"
            r"Konto registreeritud:\s*([^<]+)<br>",
            response.text,
        ):
            return Result.taken(
                extra={
                    "account_status": "pending_activation",
                    "registered_at": pending.group(1).strip(),
                }
            )

        match = re.search(
            r'<h1 class="u-box-name-txt-b text-white">(.*?)</h1>',
            response.text,
            re.DOTALL,
        )
        if not match:
            return Result.taken()

        profile_user = _text(match.group(1))
        if profile_user.casefold() != username.casefold():
            return Result.error("Profile response does not match the requested handle")

        extra: dict[str, object] = {}
        if name := re.search(r"Nimi:\s*<strong>(.*?)</strong>", response.text):
            extra["name"] = _text(name.group(1))
        if gender := re.search(r"Sugu:\s*<img[^>]*>\s*([^<]+)<br", response.text):
            extra["gender"] = html.unescape(gender.group(1)).strip()
        if user_id := re.search(r'\bvar vsID="(\d+)"', response.text):
            extra["user_id"] = int(user_id.group(1))
        if online_status := re.search(
            r'<span[^>]+title="(online|offline)"', match.group(1)
        ):
            extra["online_status"] = online_status.group(1)
        media: dict[str, str] = {}
        avatar = re.search(
            r"u-box-avatar-Pic[^>]+background-image:url\([\'\"]?([^\'\")]+)",
            response.text,
        )
        if avatar and not avatar.group(1).endswith("/images/avatar.svg"):
            media["avatar"] = urljoin("https://neanky.ee", avatar.group(1))
        return Result.taken(extra=extra, media=media)

    def process_availability(response: httpx.Response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")
        data = response.json()
        if data.get("user", {}).get("username", "").casefold() != username.casefold():
            return Result.error(
                "Availability response does not match the requested handle"
            )
        if data.get("state") == 1:
            return Result.available()
        if data.get("state") != 0:
            return Result.error("Could not verify username availability")
        try:
            return process_profile(make_request(url))
        except httpx.HTTPError as exc:
            return Result.error(exc)

    return generic_validate(
        "https://neanky.ee/p/register",
        process_availability,
        method="POST",
        data={"username": username, "type": "validateusername"},
        show_url=url,
    )


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
