from user_scanner.core.orchestrator import generic_validate, Result
from user_scanner.core.helpers import get_random_user_agent
import re as local_re

def validate_osu(user):
    url = f"https://osu.ppy.sh/users/{user}"
    show_url = f"https://osu.ppy.sh/users/{user}"

    headers = {
        "User-Agent": get_random_user_agent()
    }

    def process(response):
        if response.status_code == 200:
            extra = {}
            title_match = local_re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
            if title_match:
                title_val = title_match.group(1).replace("· player info", "").strip()
                extra["player"] = title_val

            avatar_match = local_re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
            if avatar_match:
                extra["avatar"] = avatar_match.group(1).strip()

            desc_match = local_re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
            if desc_match:
                extra["rank"] = desc_match.group(1).strip()

            return Result.taken(extra=extra)

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
