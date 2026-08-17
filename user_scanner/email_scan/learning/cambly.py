import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.cambly.com/forgotPassword"
    show_url = "https://www.cambly.com"

    payload = {
        "email": email,
    }

    headers = {
        "User-Agent": "Cambly/7.30.1 (com.cambly.cambly; Android 13)",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json; charset=UTF-8",
        "Accept-Language": "en",
        "x-cambly-interface-locale": "en_US",
        "x-cambly-entity": "googlePlay",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                return Result.taken(url=show_url)

            if response.status_code == 422:
                data = response.json()
                err = str(data.get("error", "")).lower()
                err_text = str(data.get("error_text", "")).lower()
                if "nocaptcha" in err or "captcha" in err_text:
                    return Result.taken(url=show_url)

            if response.status_code == 400:
                data = response.json()
                err = str(data.get("error", "")).lower()
                err_text = str(data.get("error_text", "")).lower()
                if "notfound" in err or "could not be found" in err_text:
                    return Result.available(url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_cambly(email: str) -> Result:
    """
    Cambly learning app email validator.
    Checks forgotPassword endpoint.
    Loud module because password reset emails are sent for registered accounts.
    """
    return await _check(email)
