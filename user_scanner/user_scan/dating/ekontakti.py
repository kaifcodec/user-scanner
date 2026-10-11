from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_ekontakti(user: str) -> Result:
    """Check e-kontakti's username validator without creating an account."""
    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected validation status: {response.status_code}")
        data = response.json()
        if isinstance(data, dict) and isinstance(data.get("response"), dict):
            availability = data["response"]
            if availability.get("usernameAvailable") is True:
                return Result.available()
            if availability.get("usernameAvailable") is False:
                return Result.taken()
        return Result.error("Unexpected username validation response")

    return impersonate_validate(
        "https://e-kontakti.fi/api/members/validate-username",
        process,
        method="POST",
        json={"text": user},
        show_url="https://e-kontakti.fi/luo-tili",
    )
