import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_suomi24(user: str) -> Result:
    """Check the shared Suomi24 account namespace without registering."""
    show_url = "https://oma.suomi24.fi/rekisteroidy"
    if not re.fullmatch(r"[a-zA-ZåäöÅÄÖ0-9][a-zA-ZåäöÅÄÖ0-9_.-]{2,23}", user):
        return Result.error("Invalid Suomi24 username format", url=show_url)

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected validation status: {response.status_code}")
        data = response.json()
        if isinstance(data, dict):
            if data.get("available") is True:
                return Result.available()
            if data.get("available") is False:
                return Result.taken()
        return Result.error("Unexpected username validation response")

    return generic_validate(
        "https://oma.suomi24.fi/rekisteroidy/vapaa",
        process,
        method="POST",
        json={"username": user},
        show_url=show_url,
    )
