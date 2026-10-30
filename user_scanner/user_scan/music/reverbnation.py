import re
import urllib.parse

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_reverbnation(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.reverbnation.com/{encoded_user}"
    show_url = f"https://www.reverbnation.com/{encoded_user}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response) -> Result:
        status = response.status_code
        text = response.text
        if status == 404 or any(ab in text for ab in ["doesn't exist", "page you were looking for"]):
            return Result.available(url=show_url)

        if status == 200 and ("| ReverbNation" in text or 'property="og:site_name" content="ReverbNation"' in text):
            extra: dict[str, str] = {}
            media: dict[str, str] = {}

            title_m = re.search(r"<title>(.*?)\s*\|\s*ReverbNation</title>", text, re.IGNORECASE)
            if title_m:
                extra["name"] = title_m.group(1).strip()

            desc_m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', text)
            if desc_m:
                desc = desc_m.group(1).strip()
                if " | " in desc:
                    parts = desc.split(" | ", 1)
                    extra["genre"] = parts[0].strip()
                    extra["location"] = parts[1].strip()
                else:
                    extra["description"] = desc

            img_m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', text)
            if img_m and "default" not in img_m.group(1).lower():
                media["avatar"] = img_m.group(1)

            return Result.taken(url=show_url, extra=extra, media=media if media else None)

        return Result.error(f"Unexpected response status {status}")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=show_url,
        follow_redirects=True,
    )

