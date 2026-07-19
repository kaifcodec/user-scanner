import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_spankbang(user):
    url = f"https://spankbang.com/profile/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile answers 200 with a "<user> Profile ... @ SpankBang"
        # title; the not-found page is a 200-less generic front page.
        if _is_profile(response.text, user):
            return Result.taken(url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return generic_validate(url, process, show_url=show_url)


def _is_profile(html: str, user: str) -> bool:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return False

    title = match.group(1).strip().lower()
    return title.startswith(user.lower() + " profile") and "spankbang" in title
