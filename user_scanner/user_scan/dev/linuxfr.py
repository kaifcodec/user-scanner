import html
import re
from urllib.parse import quote
from user_scanner.core.orchestrator import Result, generic_validate


def validate_linuxfr(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://linuxfr.org/users/{safe_user}"
    show_url = f"https://linuxfr.org/users/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())
            joined_match = re.search(r"<p>Compte créé le ([^<]+)</p>", response.text)
            if joined_match:
                extra["joined"] = joined_match.group(1).strip()
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
