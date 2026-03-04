import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_telegram(user: str) -> Result:
    url = f"https://t.me/{user}"
    show_url = f"https://t.me/{user}"

    def process(r):
        if r.status_code == 200:
            if re.search(r'<div[^>]*class="tgme_page_extra"[^>]*>', r.text):
                return Result.taken()
            else:
                return Result.available()
        return Result.error()

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
