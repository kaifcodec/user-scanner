import html
import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_gefragt_net(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://gefragt.net/user/{encoded_user}"
    show_url = f"https://gefragt.net/user/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            text = response.text

            # Question2Answer profile activity heading or username element confirms profile existence
            act_match = re.search(r'<span id="activity">\s*Aktivit[äa]t von (.*?)\s*</span>', text, re.IGNORECASE)
            has_activity_form = "qa-part-form-activity" in text
            has_user_banner = "qa-upb-avatar" in text or "qa-upb-username" in text

            if act_match or (has_activity_form and has_user_banner):
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                username_match = re.search(r'<h3 class="qa-upb-username"[^>]*>(.*?)</h3>', text)
                if username_match:
                    display_name = username_match.group(1).strip()
                    if display_name and display_name.lower() != user.lower():
                        extra["display_name"] = display_name

                points_match = re.search(r'<span class="qa-uf-user-points">([^<]+)</span>', text)
                if points_match:
                    extra["points"] = points_match.group(1).strip()

                rank_match = re.search(r'<span class="qa-uf-user-rank">([^<]+)</span>', text)
                if rank_match:
                    extra["rank"] = rank_match.group(1).strip()

                # Avatar image
                avatar_match = re.search(r'<img[^>]+class="[^"]*qa-lazy-img[^"]*"[^>]+data-src="([^"]+)"', text)
                if avatar_match:
                    avatar_src = html.unescape(avatar_match.group(1))
                    if avatar_src.startswith("../"):
                        avatar_src = f"https://gefragt.net/{avatar_src[3:]}"
                    media["avatar"] = avatar_src

                return Result.taken(url=show_url, extra=extra, media=media)

            return Result.available(url=show_url)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
