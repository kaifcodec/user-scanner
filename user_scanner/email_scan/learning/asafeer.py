import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://3asafeer.com/caller.php"
    show_url = "https://3asafeer.com"

    params = {
        "page": "user",
        "task": "forgotPass",
        "eml": email,
        "format": "json",
    }

    headers = {
        "User-Agent": "okhttp/5.3.2",
        "Accept-Encoding": "gzip",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                result_val = data.get("result")
                if result_val == "success":
                    return Result.taken(url=show_url)
                elif result_val == "failed":
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_asafeer(email: str) -> Result:
    """
    3Asafeer (مدرسة عصافير) email validator. Checks forgotPass endpoint.
    Loud module because it sends a password reset email when account exists.
    """
    return await _check(email)
