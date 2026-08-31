import secrets
import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    token_url = "https://e2p-okapi.api.okcupid.com/graphql/AnonAuthToken"
    validate_url = "https://e2p-okapi.api.okcupid.com/graphql/ValidateEmail"
    show_url = "https://okcupid.com"

    device_id = secrets.token_hex(11)

    headers = {
        "User-Agent": "Android 115.1.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
        "x-apollo-operation": "AnonAuthToken",
        "x-okcupid-device-id": f"Android; Pixel 6; 13; {device_id};",
        "x-okcupid-app": "OkCupid Android App 115.1.0",
        "x-okcupid-platform": "Android",
        "x-okcupid-version": "115.1.0",
        "x-okcupid-locale": "en-US",
        "x-match-useragent": "OkCupid/115.1.0 REL/13",
        "x-okcupid-auth-v": "1",
        "x-okcupid-emulator": "false",
        "x-emb-path": "/graphql/AnonAuthToken",
    }

    payload_token = {
        "operationName": "AnonAuthToken",
        "variables": {
            "input": {
                "deviceId": device_id,
                "siteCode": 36,
            }
        },
        "query": "mutation AnonAuthToken($input: AuthAnonymousInput!) { authAnonymous(input: $input) { token } }",
        "extensions": {
            "clientLibrary": {
                "name": "apollo-kotlin",
                "version": "4.4.3",
            }
        },
    }

    async with httpx.AsyncClient() as client:
        try:
            token_resp = await client.post(token_url, json=payload_token, headers=headers, timeout=6.0)

            if token_resp.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if token_resp.status_code != 200:
                return Result.error(
                    f"Unexpected token status: {token_resp.status_code}, report it via GitHub issues",
                    url=show_url,
                )

            token_data = token_resp.json()
            token = token_data.get("data", {}).get("authAnonymous", {}).get("token")

            if not token:
                return Result.error("Could not obtain anonymous auth token", url=show_url)

            headers_validate = headers.copy()
            headers_validate["authorization"] = token
            headers_validate["x-apollo-operation"] = "ValidateEmail"
            headers_validate["x-emb-path"] = "/graphql/ValidateEmail"

            async def check(address: str) -> bool | Result:
                payload = {
                    "operationName": "ValidateEmail",
                    "variables": {"email": address},
                    "query": "query ValidateEmail($email: String!) { auth { isEmailValid(email: $email) } }",
                    "extensions": {
                        "clientLibrary": {
                            "name": "apollo-kotlin",
                            "version": "4.4.3",
                        }
                    },
                }
                response = await client.post(
                    validate_url,
                    json=payload,
                    headers=headers_validate,
                    timeout=6.0,
                )

                if response.status_code == 429:
                    return Result.error("Rate limited", url=show_url)

                if response.status_code != 200:
                    return Result.error(
                        f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                        url=show_url,
                    )

                is_valid = response.json().get("data", {}).get("auth", {}).get("isEmailValid")
                if isinstance(is_valid, bool):
                    return is_valid

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            is_valid = await check(email)
            if isinstance(is_valid, Result):
                return is_valid

            if is_valid:
                return Result.available(url=show_url)

            domain = email.rsplit("@", 1)[-1]
            probe = await check(f"{secrets.token_hex(16)}@{domain}")
            if isinstance(probe, Result):
                return probe

            if probe is False:
                return Result.available(
                    reason=f"OkCupid rejects registrations from '{domain}'",
                    url=show_url,
                )

            return Result.taken(url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_okcupid(email: str) -> Result:
    """
    OkCupid dating app email validator.
    Fetches an anonymous token and checks the ValidateEmail GraphQL query.
    """
    return await _check(email)
