import re
from user_scanner.core.orchestrator import Result, generic_validate


def validate_coderlegion(user):
    url = f"https://coderlegion.com/user/{user}"
    show_url = f"https://coderlegion.com/user/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if response.status_code == 200:
            extra = {}
            html = response.text
            try:
                # Extract name
                name_match = re.search(r'<h1 class="profile-name">([^<]+)</h1>', html)
                if name_match:
                    extra["name"] = name_match.group(1).strip()

                # Extract headline
                headline_match = re.search(r'<div class="profile-headline">([^<]+)</div>', html)
                if headline_match:
                    extra["headline"] = headline_match.group(1).strip()

                # Extract joined date
                joined_match = re.search(r'<span class="profile-joined">Joined ([^<]+)</span>', html)
                if joined_match:
                    extra["joined"] = joined_match.group(1).strip()

                # Extract avatar URL
                avatar_match = re.search(r'<div class="profile-avatar">\s*<a[^>]+>\s*<img[^>]+src="([^"]+)"', html)
                if avatar_match:
                    avatar_url = avatar_match.group(1)
                    if avatar_url.startswith("../"):
                        avatar_url = "https://coderlegion.com/" + avatar_url.lstrip("../")
                    extra["avatar"] = avatar_url.replace("&amp;", "&")

                # Extract stats
                points_match = re.search(r'<strong>([^<]+)</strong> Points', html)
                if points_match:
                    extra["points"] = points_match.group(1).strip()

                badges_match = re.search(r'<strong>([^<]+)</strong> Badges', html)
                if badges_match:
                    extra["badges"] = badges_match.group(1).strip()

                followers_match = re.search(r'<strong>([^<]+)</strong> Followers', html)
                if followers_match:
                    extra["followers"] = followers_match.group(1).strip()

                following_match = re.search(r'<strong>([^<]+)</strong> Following', html)
                if following_match:
                    extra["following"] = following_match.group(1).strip()

            except Exception:
                pass
            return Result.taken(extra=extra)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, timeout=15.0)
