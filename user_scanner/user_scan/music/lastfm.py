import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_lastfm(user: str) -> Result:
    url = f"https://www.last.fm/user/{quote(user, safe='')}"

    def process(response) -> Result:
        text = response.text
        text_lower = text.lower()

        if "<title>client challenge</title>" in text_lower:
            return Result.error("Blocked by Last.fm client challenge")
        if (
            response.status_code in (503, 600)
            or "temporarily unavailable" in text_lower
        ):
            return Result.error(
                "Last.fm user profile service temporarily unavailable", url=url
            )
        if (
            response.status_code == 404
            or "<title>page not found | last.fm</title>" in text_lower
            or "page not found | last.fm" in text_lower
        ):
            return Result.available(url=url)
        if response.status_code == 200 and 'class="header-title"' in text:
            extra: dict[str, str] = {}
            media: dict[str, str] = {}
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
            return Result.taken(extra=extra, media=media if media else None, url=url)
        return Result.error(
            f"HTTP {response.status_code} without Last.fm profile markers", url=url
        )

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)

