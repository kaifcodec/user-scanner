from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
import re


def validate_thesimsresource(user: str) -> Result:
    url = f"https://www.thesimsresource.com/members/{user}/"
    show_url = url

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if response.status_code in (403, 429):
            return Result.error("Blocked by anti-bot protection")
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        text = response.text
        final_url = str(response.url)

        if final_url.rstrip("/") == "https://www.thesimsresource.com" or "Welcome to The Sims Resource!" in text:
            return Result.available()

        member_id = re.search(r'data-member-id="(\d+)"', text)
        if not member_id:
            return Result.error("Unexpected response")

        extra = {"member_id": member_id.group(1)}
        media = {}

        name_match = re.search(r'<a class="current" href="/members/[^"]+">([^<]+)</a>', text)
        if name_match:
            extra["username"] = name_match.group(1).strip()

        flag_match = re.search(r'class="profile-flag[^"]*" title="([^"]+)"', text)
        if flag_match:
            location = flag_match.group(1).strip()
            if location.lower().startswith("i am from "):
                location = location[10:].strip()
            extra["location"] = location

        for label in ("Creations", "Downloads", "Pageviews"):
            match = re.search(
                r'<span class="stats-size">([\d,]+)</span>\s*'
                rf'<span class="created-by">{label}</span>',
                text,
            )
            if match:
                extra[label.lower()] = int(match.group(1).replace(",", ""))

        avatar_match = re.search(r'<img class="profile-avatar"[^>]*data-src="([^"]+)"', text)
        if avatar_match and "defaultavatar" not in avatar_match.group(1):
            src = avatar_match.group(1)
            if not src.startswith("http"):
                src = f"https://www.thesimsresource.com{src}"
            media["avatar"] = src

        banner_match = re.search(r'<img class="profile-banner[^"]*"[^>]*data-src="([^"]+)"', text)
        if banner_match and "defaultbanner" not in banner_match.group(1):
            src = banner_match.group(1)
            if not src.startswith("http"):
                src = f"https://www.thesimsresource.com{src}"
            media["banner"] = src

        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)
