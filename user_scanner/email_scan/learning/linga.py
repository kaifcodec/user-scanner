import base64
import hashlib
import json
import time

import httpx

from user_scanner.core.result import Result

_APP_VERSION = "3.5.2/275"
_SIGNING_KEY = (
    "UDNuWUUwaXplRzdEWHVOTEg4TkJVOGJMZXBGemE0VnczS2svMXg5ZnZVM2ZQVXEyd1FzbG"
    "NFQ1ZhSm1tMVJ0agpKT1VVZ3FyNTB3c3hvU05Ub3M1SWFyL0V5ajgyellZcncwR3dkYWl0"
    "djA1ZklLNi8vQUY2WC9kYTdqZkRWSjYrCnovdUNDZz09"
)


def _signature(body: str, timestamp: str) -> str:
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    value = (
        f"web_{_APP_VERSION}_{_SIGNING_KEY}_scanner_{timestamp}__"
        f"POST_/recovery_{body_hash}"
    )
    value = base64.b64encode(value.encode()).decode()[::-1]
    value = value[:5] + "XYZ" + value[5:]
    value = value[3:] + value[:3]
    value = value.translate(str.maketrans("aeiouAEIOU", "XXXXXXXXXX"))
    half = len(value) // 2
    return hashlib.sha256((value[half:] + value[:half]).encode()).hexdigest()


async def validate_linga(email: str) -> Result:
    """Check Linga's reset endpoint. Sends email for registered accounts."""
    url = "https://app.linga.io/api/v2/recovery"
    body = json.dumps({"email": email}, separators=(",", ":"))
    timestamp = str(int(time.time() // 60))
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-linga-platform": "web",
                    "x-linga-appver": _APP_VERSION,
                    "x-linga-device-id": "scanner",
                    "x-linga-timezone-offset": timestamp,
                    "x-linga-signature": _signature(body, timestamp),
                },
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=url)
            if response.status_code not in (200, 404):
                return Result.error(
                    f"Unexpected response status: {response.status_code}", url=url
                )

            data = response.json()
            if response.status_code == 404 and data.get("message") == "Not found":
                return Result.available(url="https://linga.io")
            if response.status_code == 200 and data.get("message") == "Email was sent":
                return Result.taken(url="https://linga.io")
            return Result.error("Unexpected response body", url=url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=url)
