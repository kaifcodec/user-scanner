import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:

    url = f"https://api.allen-live.in/api/v1/user/identities/{email}"
    show_url = "https://allen.in"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'x-client-type': "mweb",
        'Origin': "https://allen.in",
        'Referer': "https://allen.in/",
    }

    params = {
        'communicable': "true",
        'identity_type': "EMAIL"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return Result.error("Blocked by Allen WAF (403)")

            data = response.json()
            reason = data.get("reason", "")

            # status 200 + reason "OK" means registered
            if data.get("status") == 200 and reason == "OK":
                identities = data.get("data", {}).get("identities", [])
                masked_phone = None

                # masked phone in the identities list
                for item in identities:
                    if item.get("identity_type") == "PHONE":
                        masked_phone = item.get("identity_value")
                        break

                if masked_phone:
                    return Result.taken(url=show_url, extra=f"Phone: +91{masked_phone}")
                return Result.taken(url=show_url)

            # status 200 + "Invalid email" means not registered
            if "Invalid email" in reason:
                return Result.available(url=show_url)

            return Result.error(f"Unknown response reason: {reason}")

    except Exception as e:
        return Result.error(e)


async def validate_allen(email: str) -> Result:
    return await _check(email)
