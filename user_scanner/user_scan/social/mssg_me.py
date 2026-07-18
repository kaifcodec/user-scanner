from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_mssg_me(user: str) -> Result:
    url = f"https://mssg.me/{user}"
    show_url = f"https://mssg.me/{user}"

    def process(r):
        # Claimed user redirects to a subdomain, but since we set follow_redirects=False,
        # it returns 302 Found (or 301, 307). Unclaimed user returns 404.
        if r.status_code == 404:
            return Result.available()

        if r.status_code in (200, 301, 302, 307, 308):
            return Result.taken()

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=False
    )
