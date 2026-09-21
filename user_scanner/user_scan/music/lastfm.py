import re
from urllib.parse import quote

from user_scanner.core.orchestrator import Result, generic_validate


def validate_lastfm(user: str) -> Result:
    url = f"https://www.last.fm/user/{quote(user, safe='')}"

    def process(response):
        text = response.text
        text_lower = text.lower()

        if "<title>client challenge</title>" in text_lower:
            return Result.error("Blocked by Last.fm client challenge")
        if "<title>page not found | last.fm</title>" in text_lower:
            return Result.available()
        if response.status_code == 200 and 'class="header-title"' in text:
            extra = {}
            media = {}
            display_name_match = re.search(
                r'class="header-title-display-name">\s*([^<\n\r]+)', text
            )
            if display_name_match:
                extra["display_name"] = display_name_match.group(1).strip()
            since_match = re.search(r"scrobbling since\s*([^<\n\r]+)", text)
            if since_match:
                extra["scrobbling_since"] = since_match.group(1).strip()
            for label in ("Scrobbles", "Artists"):
                if match := re.search(
                    rf"{label}.*?<p[^>]*>.*?<a[^>]*>([^<]+)</a>", text, re.DOTALL
                ):
                    extra[label.lower()] = match.group(1).strip()
            avatar_match = re.search(
                r'src="([^"]+)"[^>]*alt="Avatar for [^"]+"[^>]*itemprop="image"',
                text,
            )
            if avatar_match:
                media["avatar"] = avatar_match.group(1).strip()
            return Result.taken(extra=extra, media=media)
        return Result.error(
            f"HTTP {response.status_code} without Last.fm profile markers"
        )

    return generic_validate(url, process, show_url=url)
