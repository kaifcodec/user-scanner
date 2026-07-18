import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_crowdin(user: str) -> Result:
    url = f"https://crowdin.com/profile/{user}"
    show_url = f"https://crowdin.com/profile/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            if "Page Not Found - Crowdin" in r.text:
                return Result.available()

            extra = {}
            title_match = re.search(r"<title>([^<]+)</title>", r.text)
            if title_match:
                title_text = title_match.group(1).replace("– Crowdin", "").replace("— Crowdin", "").strip()
                match = re.search(r"^([^(]+)\(([^)]+)\)$", title_text)
                if match:
                    extra["display_name"] = match.group(1).strip()
                    extra["username"] = match.group(2).strip()
                else:
                    extra["display_name"] = title_text

            return Result.taken(extra=extra)

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
