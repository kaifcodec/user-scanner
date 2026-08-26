import re
import urllib.parse
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result

def validate_letterboxd(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://letterboxd.com/{encoded_user}/"
    show_url = f"https://letterboxd.com/{encoded_user}/"

    def process(response) -> Result:
        if response.status_code == 404:
            if "Letterboxd - Not Found" in response.text or "Page not found" in response.text or "404" in response.text:
                return Result.available(url=show_url)
            return Result.error("404 received without expected not-found markers")

        if response.status_code == 200:
            user_lower = user.lower()
            text_lower = response.text.lower()

            if (
                f"letterboxd.com/{user_lower}/" in text_lower
                or f'data-person="{user_lower}"' in text_lower
                or 'class="profile' in text_lower
                or "person-summary" in text_lower
            ):
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                title_match = re.search(r'<meta property="og:title" content="([^"]+)"', response.text)
                if title_match:
                    extra["name"] = title_match.group(1).replace("’s profile", "").replace("'s profile", "").replace("• Letterboxd", "").strip()

                desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
                if desc_match:
                    extra["bio"] = desc_match.group(1).strip()

                avatar_match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
                if avatar_match:
                    media["avatar"] = avatar_match.group(1).strip()

                return Result.taken(url=show_url, extra=extra, media=media)

            if "Letterboxd - Not Found" in response.text or "Page not found" in response.text:
                return Result.available(url=show_url)

            return Result.error("Unable to verify Letterboxd profile content")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return impersonate_validate(
        url,
        process,
        warmup_url="https://letterboxd.com/",
        impersonate="chrome120",
        show_url=show_url,
    )
