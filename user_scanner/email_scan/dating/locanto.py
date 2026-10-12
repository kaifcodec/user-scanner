from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.locanto.org/api/ajax/general"
    show_url = "https://www.locanto.org"

    payload = {
        "action": "register_attempt",
        "email": email,
        "is_dol": "true",
    }

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.locanto.org",
        "Referer": "https://www.locanto.org/g/dol/signup/?continue=https%3A%2F%2Fwww.locanto.org%2Fg%2Fdol%2Fdiscover%2F",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = await impersonate_request_async(
            url,
            method="POST",
            data=payload,
            headers=headers,
            impersonate="chrome",
        )

        if response.status_code == 403:
            return Result.error("Caught by Cloudflare WAF (403)", url=show_url)

        if response.status_code == 429:
            return Result.error("Rate limited", url=show_url)

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                return Result.error("Invalid JSON response", url=show_url)

            if not isinstance(data, dict):
                return Result.error("Unexpected response body format", url=show_url)

            if data.get("success") is True:
                return Result.available(url=show_url)

            text = str(data.get("text", "")).lower()
            if data.get("email_exists") is True or "already exists" in text or "something went wrong" in text:
                return Result.taken(url=show_url)

            return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

        return Result.error(
            f"Unexpected response status: {response.status_code}, report it via GitHub issues",
            url=show_url,
        )

    except Exception as e:
        return Result.error(e, url=show_url)


async def validate_locanto(email: str) -> Result:
    """
    #Dating by Locanto email validator.
    Checks register_attempt ajax endpoint for #Dating (Dating Only / DOL).
    """
    return await _check(email)
