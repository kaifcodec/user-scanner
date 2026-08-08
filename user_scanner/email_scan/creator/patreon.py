import json

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

# Auth steps Patreon returns for an address that already has an account:
# "password" for a local login, "sso_required" when the account can only be
# reached through a social provider.
_TAKEN_STEPS = ("password", "sso_required")


async def _check(email: str) -> Result:
    url = "https://www.patreon.com/api/auth"
    show_url = "https://patreon.com"

    params = {
        'include': "user.null",
        'fields[user]': "[]",
        'json-api-version': "1.0",
        'json-api-use-default-includes': "false"
    }

    payload = json.dumps({
        "data": {
            "type": "genericPatreonApi",
            "attributes": {
                "patreon_auth": {"email": email, "allow_account_creation": False},
                "auth_context": "auth",
                "ru": "https://www.patreon.com/home",
            },
            "relationships": {},
        }
    })

    headers = {
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'content-type': "application/vnd.api+json",
        'sec-gpc': "1",
        'accept-language': "en-US,en;q=0.7",
        'origin': "https://www.patreon.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.patreon.com/login"
    }

    try:
        response = await impersonate_request_async(
            url, "POST", params=params, data=payload, headers=headers
        )

        if response.status_code != 200:
            return Result.error(f"Status {response.status_code}, report it via GitHub issues")

        data = response.json()
        attributes = (data.get("data") or {}).get("attributes") or {}
        next_step = attributes.get("next_auth_step")

        if next_step in _TAKEN_STEPS:
            providers = attributes.get("supported_sso_providers") or []
            return Result.taken(
                url=show_url,
                extra={
                    "login_method": "SSO" if next_step == "sso_required" else "password",
                    "sso_providers": ", ".join(providers),
                },
            )

        if next_step == "signup":
            return Result.available(url=show_url)

        return Result.error("Unexpected auth step, report it via GitHub issues")

    except Exception as e:
        return Result.error(f"unexpected exception: {e}")


async def validate_patreon(email: str) -> Result:
    return await _check(email)
