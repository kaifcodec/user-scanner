import uuid

import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://autobizline.com/secondline/user/has_user/"
    show_url = "https://autobizline.com"

    headers = {
        "User-Agent": "okhttp/4.10.0",
        "Accept-Encoding": "gzip",
    }

    payload = {
        "api_token": "S(FNMSLDFKSD)FLKSlsdflkladf09asdfsafdasdf90123iksf=!@*#",
        "from_channel": "android",
        "device_id": str(uuid.uuid4()),
        "user_number": email,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                result_status = data.get("result")

                if result_status == "success":
                    has_user = data.get("has_user")
                    has_account = data.get("has_account")

                    if has_user == "yes" or has_account == "yes":
                        return Result.taken(url=show_url)

                    if has_user == "no" and has_account == "no":
                        return Result.available(url=show_url)

                if result_status == "failed":
                    return Result.error("API error / request failed", url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_secondline(email: str) -> Result:
    """
    SecondLine email validator.
    Checks user/has_user API endpoint.
    """
    return await _check(email)
