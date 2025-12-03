import re
from user_scanner.core.orchestrator import generic_validate


def validate_telegram(user: str) -> int:
    """
    Checks if a Telegram username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """
    url = f"https://t.me/{user}"

    def process(r):
        if r.status_code == 200:
            return 0 if re.search(r'<div[^>]*class="tgme_page_extra"[^>]*>', r.text) else 1
        return 2

    return generic_validate(url, process, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_telegram(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
