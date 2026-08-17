from urllib.parse import quote
import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = f"https://api.classdojo.com/api/user/emailValidation/{quote(email)}"
    show_url = "https://www.classdojo.com"

    params = {
        "skipDomainValidation": "false",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; WayDroid x86_64 Device Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/111.0.5563.116 Safari/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-client-identifier": "Android",
        "x-client-version": "8.80.0",
        "x-sign-attachment-urls": "true",
        "x-client-os-version": "33",
        "x-device-id": "fb125fbaf088ff2d",
        "x-client-language": "en-US",
        "accept-language": "en",
        "x-rn-request": "true",
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                is_available = data.get("isAvailableForSignUp")

                if is_available is False:
                    extra = {}
                    if "entityType" in data:
                        extra["entity_type"] = data["entityType"]
                    if "isPasswordless" in data:
                        extra["is_passwordless"] = data["isPasswordless"]
                    if "hasMandatorySSO" in data:
                        extra["has_mandatory_sso"] = data["hasMandatorySSO"]
                    if "oidcProviders" in data and data["oidcProviders"]:
                        extra["oidc_providers"] = data["oidcProviders"]

                    return Result.taken(extra=extra if extra else None, url=show_url)

                elif is_available is True:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_classdojo(email: str) -> Result:
    """
    ClassDojo learning app email validator.
    Checks emailValidation endpoint and extracts metadata into extra.
    """
    return await _check(email)
