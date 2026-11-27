import html
import re
from urllib.parse import quote
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result


def validate_greasyfork(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://greasyfork.org/en/users/{safe_user}"
    show_url = f"https://greasyfork.org/en/users/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())
            bio_match = re.search(r'<section id="user-profile"[^>]*>\s*<p>(.*?)</p>', response.text, re.DOTALL)
            if bio_match:
                bio_clean = re.sub(r"<[^>]+>", "", bio_match.group(1)).strip()
                if bio_clean:
                    extra["bio"] = html.unescape(bio_clean)
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)
