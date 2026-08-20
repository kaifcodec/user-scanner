from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.orchestrator import Result, generic_validate


def validate_snapchat(user):
    url = f"https://www.snapchat.com/@{user}"
    show_url = f"https://www.snapchat.com/@{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "upgrade-insecure-requests": "1",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            media = {}
            next_data = parse_next_pages_data(response.text) or {}
            user_profile = (
                next_data.get("props", {})
                .get("pageProps", {})
                .get("userProfile", {})
            )
            u_info = user_profile.get("userInfo", {})
            if u_info:
                if u_info.get("displayName"):
                    extra["display_name"] = u_info.get("displayName")
                if u_info.get("snapcodeImageUrl"):
                    media["snapcode"] = u_info.get("snapcodeImageUrl")
            return Result.taken(extra=extra, media=media)
        else:
            return Result.error(f"HTTP {response.status_code}")

    return generic_validate(
        url, process, show_url=show_url, headers=headers, follow_redirects=True
    )
