import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_geocaching(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.geocaching.com/p/default.aspx?u={encoded_user}"
    show_url = f"https://www.geocaching.com/p/default.aspx?u={encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            if "Error 404" in response.text or "404" in response.text or "DNF" in response.text:
                return Result.available(url=show_url)
            return Result.error("404 received without expected not-found markers")

        if response.status_code == 200:
            user_lower = user.lower()
            text_lower = response.text.lower()

            if (
                f"default.aspx?u={user_lower}" in text_lower
                or "hax-profile" in response.text
                or "lblmembername" in text_lower
                or "window.publicprofile" in text_lower
            ):
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                name_match = re.search(r'<span id="[^"]*lblMemberName">([^<]+)</span>', response.text)
                if name_match:
                    extra["name"] = name_match.group(1).strip()

                avatar_match = re.search(r'id="[^"]*uxProfilePhoto"[^>]+src="([^"]+)"', response.text)
                if avatar_match:
                    avatar_url = avatar_match.group(1).strip()
                    if avatar_url.startswith("/"):
                        avatar_url = f"https://www.geocaching.com{avatar_url}"
                    media["avatar"] = avatar_url

                banner_match = re.search(r'id="[^"]*uxBannerPhoto"[^>]+src="([^"]+)"', response.text)
                if banner_match:
                    banner_url = banner_match.group(1).strip()
                    if banner_url.startswith("/"):
                        banner_url = f"https://www.geocaching.com{banner_url}"
                    media["banner"] = banner_url

                return Result.taken(url=show_url, extra=extra, media=media)

            if "Error 404" in response.text or "DNF" in response.text:
                return Result.available(url=show_url)

            return Result.error("Unable to verify Geocaching profile structure")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
