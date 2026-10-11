from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_happypancake(user: str) -> Result:
    """Use HappyPancake Sweden's username availability check."""
    url = "https://api.happypancake.se/accounts/validateusername/" + quote(user, safe="")

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected validation status: {response.status_code}")
        data = response.json()
        if isinstance(data, dict):
            if data.get("valid") is True and data.get("message") is None:
                return Result.available()
            if data.get("valid") is False and data.get("message") == "in-use":
                return Result.taken()
            if data.get("message") == "invalid-format":
                return Result.error("Invalid HappyPancake username format")
        return Result.error("Unexpected username validation response")

    return generic_validate(
        url, process, show_url="https://www.happypancake.se/signup"
    )
