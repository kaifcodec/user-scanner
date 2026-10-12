from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_deitti(user: str) -> Result:
    """Use Deitti.net's inline username check without submitting registration."""
    show_url = "https://www.deitti.net/tili/liity"
    if (
        not 3 <= len(user) <= 25
        or not any(char.isalpha() for char in user)
        or not all(char.isalpha() or char in "0123456789_.#!?() -" for char in user)
    ):
        return Result.error("Invalid Deitti.net username format", url=show_url)

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected validation status: {response.status_code}")
        data = response.json()
        if isinstance(data, dict):
            if data.get("isValid") is True and not data.get("error"):
                return Result.available()
            if (
                data.get("isValid") is False
                and data.get("error") == "Nimimerkki on jo käytössä."
            ):
                return Result.taken()
        return Result.error("Unexpected username validation response")

    return generic_validate(
        "https://www.deitti.net/ajax/validate/username",
        process,
        method="POST",
        data={"validate": user},
        headers={"X-Requested-With": "XMLHttpRequest"},
        show_url=show_url,
    )
