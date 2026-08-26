import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_wakatime(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://wakatime.com/@{encoded_user}"
    show_url = f"https://wakatime.com/@{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            if "Page Not Found" in response.text or "404: Not Found" in response.text or "404" in response.text:
                return Result.available(url=show_url)
            return Result.error("404 received without expected not-found markers")

        if response.status_code == 200:
            if f"@{user.lower()}" in response.text.lower() or "wakatime.com/@" in response.text:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                title_match = re.search(r'<title>(.+?)</title>', response.text)
                if title_match:
                    title_clean = title_match.group(1).replace("- WakaTime", "").strip()
                    extra["title"] = title_clean

                desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
                if desc_match:
                    extra["bio"] = desc_match.group(1).strip()

                img_match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
                if img_match:
                    media["avatar"] = img_match.group(1).strip()

                return Result.taken(url=show_url, extra=extra, media=media)

            if "Page Not Found" in response.text or "404: Not Found" in response.text:
                return Result.available(url=show_url)

            return Result.error("Unable to verify WakaTime profile structure")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
