from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_ekontakti(user: str) -> Result:
    """Check e-kontakti's username validator without creating an account."""
    show_url = "https://e-kontakti.fi/luo-tili"
    if not 4 <= len(user) <= 14:
        return Result.error("Username must be 4-14 characters long", url=show_url)

    def process(response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected validation status: {response.status_code}", url=show_url)

        try:
            data = response.json()
        except Exception:
            text = response.text
            if "USERNAME_TOO_LONG" in text:
                return Result.error("Username exceeds maximum length of 14 characters", url=show_url)
            if "USERNAME_TOO_SHORT" in text:
                return Result.error("Username must be at least 4 characters long", url=show_url)
            return Result.error("Failed to parse E-kontakti validation response", url=show_url)

        if isinstance(data, dict) and isinstance(data.get("response"), dict):
            availability = data["response"]
            if availability.get("usernameAvailable") is True:
                return Result.available(url=show_url)
            if availability.get("usernameAvailable") is False:
                return Result.taken(url=show_url)

        return Result.error("Unexpected username validation response", url=show_url)

    return impersonate_validate(
        "https://e-kontakti.fi/api/members/validate-username",
        process,
        method="POST",
        json={"text": user},
        show_url=show_url,
    )
