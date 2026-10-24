import html
import re
from urllib.parse import quote
from user_scanner.core.orchestrator import Result, generic_validate


def validate_clojars(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://clojars.org/users/{safe_user}"
    show_url = f"https://clojars.org/users/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())

            proj_match = re.search(r"<h2>Projects</h2>\s*<ul>(.*?)</ul>", response.text, re.DOTALL)
            if proj_match:
                projects = re.findall(r"""href=["']/([^"']+)["']""", proj_match.group(1))
                if projects:
                    extra["projects_count"] = len(projects)
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
