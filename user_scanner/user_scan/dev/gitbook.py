from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_gitbook(user: str) -> Result:
    url = f"https://{user}.gitbook.io/"
    show_url = f"https://{user}.gitbook.io/"

    def process(r):
        if r.status_code == 404:
            if "Content owner not found" in r.text or "not found" in r.text.lower():
                return Result.available()

        if r.status_code in (200, 301, 302, 307):
            return Result.taken()

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=False
    )
