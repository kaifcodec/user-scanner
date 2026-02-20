import httpx
import json
import uuid
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://moz.com"
    url = "https://moz.com/app-api/jsonrpc/user.create.validate"

    rpc_id = str(uuid.uuid4())

    payload = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "user.create.validate",
        "params": {
            "data": {
                "create_session": True,
                "verification_email_redirect": "/checkout/freetrial/billing-payment/pro_medium/monthly",
                "user": {
                    "email": email,
                    "password": "W3n3v3r_t0uch3d_s0ftn33s"
                }
            }
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'origin': "https://moz.com",
        'referer': "https://moz.com/checkout/freetrial/signup/pro_medium/monthly",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            result_data = data.get("result", {})
            errors = result_data.get("errors", [])

            if not errors:
                return Result.available(url=show_url)

            if any(err.get("data", {}).get("issue") == "param-is-duplicate" for err in errors):
                return Result.taken(url=show_url)

            return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_moz(email: str) -> Result:
    return await _check(email)
