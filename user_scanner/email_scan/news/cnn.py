import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://audience.cnn.com/core/api/1/identity"

    payload = {
        "identityRequests": [
            {
                "identityType": "EMAIL",
                "principal": email,
                "credential": "th3_sil3nt_fir3wall_hid3s_most"
            }
        ]
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'x-client-application': "Android|Android 10|Chrome 144.0.0.0",
        'Origin': "https://edition.cnn.com",
        'Referer': "https://edition.cnn.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            body = response.text

            if "identity.already.in.use" in body:
                return Result.taken()

            if "cnn.createprofile" in body and "cnn.updatepassword" in body:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out!")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_cnn(email: str) -> Result:
    return await _check(email)
