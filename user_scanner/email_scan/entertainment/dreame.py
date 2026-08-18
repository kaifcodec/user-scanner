import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://wap-api.dreame.com/Login/loginWithEmail"
    show_url = "https://www.dreame.com"

    dummy_password = (
        "jnW1Pjcoiyrg+dkxNw8SsMdrWC3Iho1qwaUEwXKeC5cXvvySR0iaYJLLYBNSceDB6KSQoNn9"
        "BVk9ZzIpSr8iAkwnNp/Ou0HbXcPXZiLK6t+b/DvlWVxaadaOke15mibcYWgg82C8BBWSHMX6"
        "NyWs2YkVitTlWVCZ22rNz1ahFaQ="
    )

    params = {
        "systemFlag": "android",
        "channel": "dreamepmian-173",
        "product": "1",
        "osType": "2",
        "userKey": "",
        "language": "en",
        "user": email,
        "password": dummy_password,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "origin": "https://www.dreame.com",
        "referer": "https://www.dreame.com/",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                msg = str(data.get("msg", "")).lower()

                if "account or password is incorrect" in msg:
                    return Result.taken(url=show_url)
                elif "has not been registered" in msg:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_dreame(email: str) -> Result:
    """
    Dreame (Dreame Media / Ebooks) email validator.
    Checks loginWithEmail endpoint with a dummy password.
    """
    return await _check(email)
