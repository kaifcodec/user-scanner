from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_ekontakti(email: str) -> Result:
    """Check e-kontakti email availability without registration or sending mail."""
    show_url = "https://e-kontakti.fi/luo-tili"
    try:
        response = await impersonate_request_async(
            "https://e-kontakti.fi/api/members/validate-email-address",
            method="POST",
            json={"text": email},
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected validation status: {response.status_code}", url=show_url
            )
        data = response.json()
        if isinstance(data, dict) and isinstance(data.get("response"), dict):
            availability = data["response"]
            if availability.get("addressIncorrectFormat") is True:
                return Result.error("Invalid e-kontakti email format", url=show_url)
            if availability.get("addressIncorrectFormat") is False:
                if availability.get("addressAlreadyInUse") is True:
                    return Result.taken(url=show_url)
                if availability.get("addressAlreadyInUse") is False:
                    return Result.available(url=show_url)
        return Result.error("Unexpected email validation response", url=show_url)
    except (RequestException, ValueError) as exc:
        return Result.error(exc, url=show_url)
