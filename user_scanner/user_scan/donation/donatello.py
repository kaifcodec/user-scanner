import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

CLOUDFLARE_BLOCK_MARKER = "Attention Required! | Cloudflare"

# Only a creator page carries its own handle in og:url; the site's own pages
# (/about, /login, /terms) answer 200 with the bare domain there instead.
OG_HANDLE_RE = re.compile(r'<meta property="og:url" content="https://donatello\.to/([^"/?]+)"')
AUTHOR_RE = re.compile(r'<meta name="author" content="([^"]+)">')


def validate_donatello(user):
    url = f"https://donatello.to/{user}"

    def process(response):
        if response.status_code == 200:
            handle_match = OG_HANDLE_RE.search(response.text)
            if not handle_match:
                return Result.error("200 without a creator page, cannot confirm the handle")

            extra = {}
            author_match = AUTHOR_RE.search(response.text)
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
