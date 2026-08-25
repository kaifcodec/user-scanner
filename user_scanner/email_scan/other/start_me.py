from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_start_me(email: str) -> Result:
    """Validate whether an email is registered on Start.me (start.me)."""
    url = f"https://start.me/users/check_email?email={email}"
    show_url = "https://start.me"
    headers = {
        "Accept": "application/json",
        "Referer": "https://start.me/users/sign_up",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = await impersonate_request_async(
            url,
            method="GET",
            headers=headers,
            impersonate="chrome",
        )

        if response.status_code == 403:
            return Result.error("Caught by Cloudflare WAF (403)", url=show_url)

        if response.status_code == 429:
            return Result.error("Rate limited by Start.me (429)", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

        data = response.json()
        if not isinstance(data, dict):
            return Result.error("Unexpected response body format", url=show_url)

        exists = data.get("exists")
        if exists is True:
            extra = {}
            if data.get("locked") is True:
                extra["account_locked"] = True
            return Result.taken(extra=extra, url=show_url)

        if exists is False:
            return Result.available(url=show_url)

        return Result.error("Missing 'exists' key in Start.me response", url=show_url)

    except Exception as e:
        return Result.error(f"Unexpected exception: {e}", url=show_url)
