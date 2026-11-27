import html
import re
from urllib.parse import quote
from user_scanner.core.orchestrator import Result, generic_validate


def validate_open_game_art(user: str) -> Result:
    safe_user = quote(user, safe="")
    url = f"https://opengameart.org/users/{safe_user}"
    show_url = f"https://opengameart.org/users/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict[str, object] = {}
            title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                if title:
                    extra["title"] = " ".join(title.split())
            id_match = re.search(r'<link rel="shortlink" href="https://opengameart\.org/user/(\d+)"', response.text)
            if id_match:
                extra["id"] = int(id_match.group(1))
            name_match = re.search(r'<meta about="/users/[^"]+" property="foaf:name" content="([^"]+)"', response.text)
            if name_match:
                extra["name"] = html.unescape(name_match.group(1).strip())
            return Result.taken(extra=extra if extra else None, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
