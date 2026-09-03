import html
import re
import urllib.parse
from user_scanner.core.orchestrator import Result
from user_scanner.core.impersonate import impersonate_validate

def validate_wikidot(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"http://www.wikidot.com/user:info/{encoded_user}"
    show_url = url

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            text = response.text
            if "User does not exist" in text or '<div class="error-block">' in text:
                return Result.available(url=show_url)

            if '<div id="user-info-area">' in text or "USERINFO.userId" in text:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                user_id_match = re.search(r'USERINFO\.userId\s*=\s*(\d+);', text)
                if user_id_match:
                    extra["user_id"] = user_id_match.group(1)

                since_match = re.search(r'<dt>Wikidot user since:</dt>\s*<dd><span[^>]*>([^<]+)</span>', text)
                if since_match:
                    extra["joined"] = since_match.group(1).strip()

                type_match = re.search(r'<dt>Account type:</dt>\s*<dd>\s*([^<\s]+)', text)
                if type_match:
                    extra["account_type"] = type_match.group(1).strip()

                karma_match = re.search(r'<dt>Karma level:</dt>\s*<dd>\s*([^<\s]+)', text)
                if karma_match:
                    extra["karma"] = karma_match.group(1).strip()

                avatar_match = re.search(r'<img[^>]+src="([^"]*avatar\.php[^"]*)"', text)
                if avatar_match:
                    media["avatar"] = html.unescape(avatar_match.group(1))

                return Result.taken(url=show_url, extra=extra, media=media)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return impersonate_validate(url, process, show_url=show_url, impersonate="chrome")
