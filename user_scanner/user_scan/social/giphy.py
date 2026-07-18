import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_giphy(user: str) -> Result:
    url = f"https://giphy.com/channel/{user}"
    show_url = f"https://giphy.com/channel/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            if "<title>404 Not Found</title>" in r.text or "404 Not Found" in r.text:
                return Result.available()

            if (
                'property="al:ios:app_name" content="Giphy"' in r.text
                or "giphy://shortcut/channel/" in r.text
            ):
                extra = {}
                title_match = re.search(r"<title>([^<]+)</title>", r.text)
                if title_match:
                    display_name = title_match.group(1).replace(" GIFs on GIPHY - Be Animated", "").strip()
                    extra["display_name"] = display_name

                desc_match = re.search(
                    r'<meta name="description" content="([^"]+)"', r.text
                )
                if desc_match:
                    extra["bio"] = desc_match.group(1).strip()

                image_match = re.search(
                    r'<meta property="og:image" content="([^"]+)"', r.text
                )
                if image_match:
                    extra["avatar_url"] = image_match.group(1).strip()

                return Result.taken(extra=extra)

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
