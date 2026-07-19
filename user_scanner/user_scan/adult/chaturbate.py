import httpx
import re
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
                return Result.taken(url=show_url)

            # Other username errors are format rejections (length, characters),
            # not an existence signal.
            if username_error:
                return Result.error(username_error, url=show_url)

            return Result.available(url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_chaturbate(user: str) -> Result:
    return await _check(user)
