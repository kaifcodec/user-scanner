import json

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_secretbenefits(user: str) -> Result:
    url = "https://www.secretbenefits.com/validations/username"
    show_url = "https://secretbenefits.com"
    params = {
        "username": user,
        "benefactor": "true",
    }

    if not _validate_string(user):
        return Result.error(
            "Username must be 5-15 characters long and contain only ASCII alphanumeric characters.",
            url=show_url,
        )

    def process(response):

        if response.is_success:
            try:
                data = response.json()
            except json.JSONDecodeError as exc:
                return Result.error(exc)

            if data.get("unique") is True:
                return Result.available(url=show_url)
            elif data.get("unique") is False:
                return Result.taken(url=show_url)
            else:
                return Result.error(
                    "Can't determine if the username is available or not.", url=show_url
                )

        else:
            return Result.error(
                f"Unexpected response status: {response.status_code}", url=show_url
            )

    return generic_validate(
        url, process, params=params, show_url=show_url, follow_redirects=True
    )


def _validate_string(s: str) -> bool:
    """
    Validate that the username length is between 5 and 15 characters
    and contains only ASCII alphanumeric characters.

    Args:
        s (str): The username string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    return 5 <= len(s) <= 15 and s.isascii() and s.isalnum()
