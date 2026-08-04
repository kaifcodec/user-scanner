import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://data.period-tracker.com/databackup/data.php"
    show_url = "https://period-tracker.com"

    params = {
        'action': "checkAccount"
    }

    payload = {
        'email': email,
        'app_type': "calendar",
        'app_platform': "android",
        'data_version': "33",
        'app_version': "12.7.6"
    }

    headers = {
        'User-Agent': "Dart/3.10 (dart:io)",
        'Accept-Encoding': "gzip"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            # Form-encoded POST request
            response = await client.post(url, params=params, data=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "NoAccount":
                    return Result.available(url=show_url)
                elif status == "Success":
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_myperiodtracker(email: str) -> Result:
    """
    My Period Tracker email validator. Checks backup account existence endpoint.
    """
    return await _check(email)
