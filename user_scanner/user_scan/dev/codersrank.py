from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
import re


def validate_codersrank(user):
    url = f"https://profile.codersrank.io/user/{user}/"
    show_url = url

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if response.status_code == 200:
            text = response.text
            if re.search(r'status:"not_found"', text):
                return Result.available()
            name_match = re.search(r'<div class="profile-head-name[^"]*"[^>]*>\s*<span>([^<]+)</span>', text)
            avatar_match = re.search(r'<div class="profile-head-avatar"><img[^>]*src="([^"]+)"', text)
            if not re.search(r'status:"(?:registered|generated)"', text) and not name_match and not avatar_match:
                return Result.error("Unexpected response")
            extra = {}
            media = {}
            if name_match:
                extra["fullname"] = name_match.group(1).strip()
            loc_match = re.search(r'class="profile-head-location[^"]*"[^>]*>.*?<span>([^<]+)</span>', text, re.S)
            if loc_match:
                extra["location"] = loc_match.group(1).strip()
            if avatar_match:
                media["avatar"] = avatar_match.group(1)
            return Result.taken(extra=extra, media=media)
        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)
