import httpx
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
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 6 Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/111.0.5563.116 Safari/537.36 YalwApp/eL.4.2.83",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.locanto.org",
        "Referer": "https://www.locanto.org/g/dol/signup/?continue=https%3A%2F%2Fwww.locanto.org%2Fg%2Fdol%2Fdiscover%2F",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
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
