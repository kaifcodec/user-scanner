import time
import httpx
from user_scanner.core.result import Result


def _generate_timestamp() -> str:
    """Generate current epoch timestamp in milliseconds."""
    return str(int(time.time() * 1000))


async def _check(email: str) -> Result:
    url = "https://ad.meetyouintl.com/v2/email_check"
    show_url = "https://www.meetyouintl.com"

    params = {
        'email': email,
        'v': "5.0.1",
        'platform': "android"
    }

    ts = _generate_timestamp()

    headers = {
        'Host': "users.meetyouintl.com",
        'User-Agent': "com.meetyou.intl/5.0.1 MeetYouClient/2.0.0 (2930501020100000)",
        'Accept-Encoding': "gzip, deflate",
        'country': "US",
        'open-person-ad': "1",
        'bundleid': "201",
        'platform': "android",
        'mode': "3",
        'syslang': "en-US",
        'zone': "0",
        'is-em': "0000300-NONE",
        'client': "0",
        'simcountry': "US",
        'lang': "en-US",
        'uregion': "singapore",
        'version': "5.0.1",
        'myclient': "2930501020100000",
        'clang': "en-US",
        'v': "5.0.1",
        'channel_id': "201",
        'syscountry': "US",
        'session-id': ts
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                code = data.get("code")
                msg = str(data.get("message", "")).lower()

                if code == 0 and "registered" not in msg:
                    return Result.available(url=show_url)
                elif code == 11001130 or "registered" in msg:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_meetyou(email: str) -> Result:
    """
    MeetYou email validator. Checks email_check endpoint for account existence.
    """
    return await _check(email)
