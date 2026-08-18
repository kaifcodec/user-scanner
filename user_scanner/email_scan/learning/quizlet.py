import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.quizlet.com/3.11/validate-email"
    show_url = "https://quizlet.com"

    params = {
        "client_id": "XbSGGchEnA",
    }

    payload = {
        "email": email,
    }

    headers = {
        "User-Agent": "QuizletAndroid/10.47 Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230901.001)",
        "Accept-Encoding": "gzip",
        "accept-language": "en-US",
        "content-type": "application/json; charset=UTF-8",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                responses = data.get("responses", [])
                if responses and isinstance(responses, list):
                    validate_data = responses[0].get("data", {}).get("validateEmail", {})
                    if "isValid" in validate_data:
                        is_valid = validate_data["isValid"]
                        if is_valid is False:
                            extra = {}
                            if validate_data.get("existingAccount"):
                                extra["existing_account"] = validate_data["existingAccount"]
                            return Result.taken(extra=extra if extra else None, url=show_url)
                        elif is_valid is True:
                            return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(
                f"Unexpected response status: {response.status_code}, report it via GitHub issues",
                url=show_url,
            )

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_quizlet(email: str) -> Result:
    """
    Quizlet learning app email validator.
    Checks validate-email endpoint and returns verdict based on isValid.
    """
    return await _check(email)
