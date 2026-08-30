import re
import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_myminifactory(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.myminifactory.com/users/{encoded_user}"
    show_url = f"https://www.myminifactory.com/users/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        if response.status_code == 404:
            if "404 Not Found" in response.text or "404" in response.text:
                return Result.available(url=show_url)
            return Result.error("404 received without expected not-found markers")

        if response.status_code == 200:
            user_lower = user.lower()
            text_lower = response.text.lower()

            if f"@{user_lower}" in text_lower or f"myminifactory.com/users/{user_lower}" in text_lower:
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                title_match = re.search(r'<title>(.+?)</title>', response.text)
                if title_match:
                    raw_title = title_match.group(1).replace("- MyMiniFactory", "").strip()
                    extra["title"] = raw_title
                    # If title format is "NAME @HANDLE", extract name
                    if f"@{user.upper()}" in raw_title.upper():
                        name_candidate = re.sub(r'@\S+', '', raw_title).strip()
                        if name_candidate:
                            extra["name"] = name_candidate

                desc_match = re.search(r'<meta name="description" content="([^"]+)"', response.text)
                if desc_match:
                    bio = desc_match.group(1).strip()
                    if bio and bio != f"- {extra.get('name', '')} @{user.upper()}":
                        extra["bio"] = bio

                img_match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
                if img_match:
                    media["avatar"] = img_match.group(1).strip()

                return Result.taken(url=show_url, extra=extra, media=media)

            if "404 Not Found" in response.text:
                return Result.available(url=show_url)

            return Result.error("Unable to verify MyMiniFactory profile structure")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
