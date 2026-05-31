from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate, Result


def validate_audiojungle(user):
    url = f"https://audiojungle.net/user/{user}"
    show_url = f"https://audiojungle.net/user/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                import re as local_re
                # 1. Location
                loc_match = local_re.search(r'<p class="t-body -size-m h-p0 h-mb0">\s*([^,\n\r]+),', response.text)
                if loc_match:
                    extra["location"] = loc_match.group(1).strip()
                # 2. Joined Date
                joined_match = local_re.search(r'Member since ([^<\n\r]+)', response.text)
                if joined_match:
                    extra["joined"] = joined_match.group(1).strip()
                # 3. Avatar
                avatar_match = local_re.search(r'class="user-info-header__user-details">\s*<img[^>]*src="([^"]+)"', response.text, local_re.DOTALL)
                if avatar_match:
                    extra["avatar"] = avatar_match.group(1).strip()
                # 4. Followers
                followers_match = local_re.search(r'href="/user/[^/]+/followers">Followers\s*<span[^>]*>([0-9]+)</span>', response.text, local_re.DOTALL)
                if followers_match:
                    extra["followers"] = int(followers_match.group(1))
                # 5. Following
                following_match = local_re.search(r'href="/user/[^/]+/following">Following\s*<span[^>]*>([0-9]+)</span>', response.text, local_re.DOTALL)
                if following_match:
                    extra["following"] = int(following_match.group(1))
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)

