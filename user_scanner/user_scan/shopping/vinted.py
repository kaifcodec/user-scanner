import difflib
import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_vinted(user: str):
    user = user.lower().strip()

    url = f"https://www.vinted.pt/member/general/search?search_text={user}"

    if not re.match(r"^[a-zA-Z0-9_.-]+$", user):
        return Result.error(
            "Usernames can only contain letters, numbers, underscores, periods and dashes"
        )

    if user.startswith(("_", "-", ".")) or user.endswith(("_", "-", ".")):
        return Result.error("Cannot start/end with a special character")

    def process(response):
        if response.status_code != 200:
            return Result.error("Invalid status code")

        pattern = r"\"login\\\":\\\"([A-Za-z0-9_.-]+)"
        search = re.findall(pattern, response.text)

        if len(search) == 0:
            return Result.available()
        elif user not in search:
            closest = difflib.get_close_matches(user, search, n=1)
            msg = f"closest: {closest[0]}" if closest else None
            return Result.available(msg)
        else:
            return Result.taken()

    return generic_validate(url, process)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    validate_vinted(user).show()
