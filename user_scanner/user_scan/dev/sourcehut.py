import re
import urllib.parse
from user_scanner.core.orchestrator import Result
from user_scanner.core.impersonate import impersonate_validate

def validate_sourcehut(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://sr.ht/~{encoded_user}/"
    show_url = f"https://sr.ht/~{encoded_user}"

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            text = response.text
            if f"<title>~{user}</title>" in text or "meta.sr.ht" in text:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                title_match = re.search(r"<title>(~[^<]+)</title>", text)
                if title_match:
                    extra["profile"] = title_match.group(1)

                avatar_match = re.search(r'src="(https://s3\.sr\.ht/meta\.sr\.ht/avatars/[^"]+)"', text)
                if avatar_match:
                    media["avatar"] = avatar_match.group(1)

                return Result.taken(url=show_url, extra=extra, media=media)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return impersonate_validate(url, process, show_url=show_url, impersonate="chrome")
