import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_lobsters(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://lobste.rs/~{encoded_user}"
    show_url = url

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            text = response.text
            if '<title>User not found | Lobsters</title>' in text or "If this user used to exist" in text:
                return Result.available(url=show_url)

            if '<div id="gravatar"' in text or 'class="avatar"' in text or '<dt>Joined</dt>' in text:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                joined_match = re.search(r'<dt>Joined</dt>\s*<dd>\s*<time[^>]*datetime="([^"]+)"', text)
                if joined_match:
                    extra["joined"] = joined_match.group(1).strip()

                karma_match = re.search(r'<dt>Karma</dt>\s*<dd>\s*(\d+)', text)
                if karma_match:
                    extra["karma"] = karma_match.group(1).strip()

                github_match = re.search(r'<a href="(https://github\.com/[^"]+)"', text)
                if github_match:
                    extra["github"] = github_match.group(1).strip()

                img_match = re.search(r'<meta property="og:image" content="([^"]+)"', text)
                if img_match:
                    img_url = img_match.group(1)
                    if img_url.startswith("/"):
                        img_url = f"https://lobste.rs{img_url}"
                    media["avatar"] = img_url

                return Result.taken(url=show_url, extra=extra, media=media)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
