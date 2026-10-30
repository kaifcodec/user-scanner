import html
import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_carbonmade(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://{encoded_user}.carbonmade.com"
    show_url = f"https://{encoded_user}.carbonmade.com"

    def process(response) -> Result:
        status = response.status_code

        if status == 404 and "not found" in response.text.lower():
            return Result.available(url=show_url)

        if status == 200:
            extra: dict[str, str] = {}
            match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
            if match:
                title = html.unescape(match.group(1)).strip()
                if title and "carbonmade" not in title.lower():
                    extra["name"] = title
            return Result.taken(url=show_url, extra=extra)

        return Result.error(f"Unexpected response status {status}", url=show_url)

    return impersonate_validate(
        url,
        process,
        show_url=show_url,
        allow_redirects=True,
    )
