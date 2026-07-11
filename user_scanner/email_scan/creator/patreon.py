import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=False) as client:
        try:
            url = "https://www.patreon.com/api/auth"
            show_url = "https://patreon.com"

            params = {
                'include': "user.null",
                'fields[user]': "[]",
                'json-api-version': "1.0",
                'json-api-use-default-includes': "false"
            }

            payload = "{\"data\":{\"type\":\"genericPatreonApi\",\"attributes\":{\"patreon_auth\":{\"email\":\"" + email + \
                "\",\"allow_account_creation\":false},\"auth_context\":\"auth\",\"ru\":\"https://www.patreon.com/home\"},\"relationships\":{}}}"

            headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
                'content-type': "application/vnd.api+json",
                'sec-ch-ua-mobile': "?0",
                'sec-gpc': "1",
                'accept-language': "en-US,en;q=0.7",
                'origin': "https://www.patreon.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://www.patreon.com/login"
            }

            response = await client.post(
                url,
                params=params,
                content=payload,
                headers=headers,
                timeout=6.0
            )

            if response.status_code != 200:
                return Result.error(f"Status {response.status_code}, report it via GitHub issues")

            data = response.json()
            next_step = data.get("data", {}).get(
                "attributes", {}).get("next_auth_step")

            if next_step == "password":
                return Result.taken(url=show_url)
            elif next_step == "signup":
                return Result.available(url=show_url)
            else:
                return Result.error("Unexpected auth step, report it via GitHub issues")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_patreon(email: str) -> Result:
    return await _check(email)
