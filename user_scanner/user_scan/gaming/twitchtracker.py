import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_twitchtracker(user: str) -> Result:
    url = f"https://twitchtracker.com/{user}"
    show_url = f"https://twitchtracker.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            if "404 Page Not Found" in response.text or "Page Not Found" in response.text or "404" in response.text:
                return Result.available()
            return Result.error("404 received without expected not-found markers")

        if response.status_code == 200:
            # Check if page is an active channel profile
            if "Streamer Overview" in response.text or f"name: '{user}'" in response.text.lower() or f"name: '{user.lower()}'" in response.text.lower():
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                rank_match = re.search(r'#([0-9,]+)\s*</div>\s*<div[^>]*>\s*RANK', response.text, re.I)
                if rank_match:
                    extra["rank"] = rank_match.group(1).replace(",", "")

                followers_match = re.search(r'([0-9,]+)\s*</div>\s*<div[^>]*>\s*FOLLOWERS', response.text, re.I)
                if followers_match:
                    extra["followers"] = followers_match.group(1).replace(",", "")

                title_match = re.search(r'<title>([^\<]+)</title>', response.text)
                if title_match:
                    extra["title"] = title_match.group(1).strip()

                avatar_match = re.search(r'<img[^>]+src="([^"]+static-cdn\.jtvnw\.net/jtv_user_pictures/[^"]+)"', response.text)
                if avatar_match:
                    media["avatar"] = avatar_match.group(1)

                return Result.taken(url=show_url, extra=extra, media=media)

            if "404 Page Not Found" in response.text or "Page Not Found" in response.text:
                return Result.available()

            return Result.error("Unable to verify TwitchTracker profile structure")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
