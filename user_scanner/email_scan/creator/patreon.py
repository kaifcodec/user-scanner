import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=False) as client:
        try:
            url = "https://www.patreon.com/api/auth"

            params = {
                'include': "user.null",
                'fields[user]': "[]",
                'json-api-version': "1.0",
                'json-api-use-default-includes': "false"
            }

            payload = "{\"data\":{\"type\":\"genericPatreonApi\",\"attributes\":{\"patreon_auth\":{\"email\":\"" + email + \
                "\",\"allow_account_creation\":false},\"auth_context\":\"auth\",\"ru\":\"https://www.patreon.com/home\"},\"relationships\":{}}}"

            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
                'Accept-Encoding': "identity",
                'content-type': "application/vnd.api+json",
                'origin': "https://www.patreon.com"
            }

            response = await client.post(
                url,
                params=params,
                content=payload,
                headers=headers
            )

            if response.status_code != 200:
                return Result.error(f"Status {response.status_code}")

            data = response.json()
            next_step = data.get("data", {}).get(
                "attributes", {}).get("next_auth_step")

            if next_step == "password":
                return Result.taken()
            elif next_step == "signup":
                return Result.available()
            else:
                return Result.error("Unexpected auth step")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_patreon(email: str) -> Result:
    return await _check(email)





