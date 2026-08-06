import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

CLOUDFLARE_BLOCK_MARKER = "Attention Required! | Cloudflare"


def validate_donatello(user):
    url = f"https://donatello.to/{user}"

    def process(response):
        if response.status_code == 200:
            extra = {}
            author_match = re.search(r'<meta name="author" content="([^"]+)">', response.text)
            if author_match:
                name = author_match.group(1).strip()
                if name.lower() != user.lower():
                    extra["name"] = name
            return Result.taken(extra=extra)

        if response.status_code == 404:
            return Result.available()

        # Cloudflare blocks whole regions from this domain; that is not a verdict.
        if response.status_code == 403 and CLOUDFLARE_BLOCK_MARKER in response.text:
            return Result.error("Blocked by Cloudflare, the site is unreachable from here")

        return Result.error(f"Unexpected status {response.status_code}")

    return impersonate_validate(url, process, show_url=url)
