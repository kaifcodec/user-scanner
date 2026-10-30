import html
import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_smugmug(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://{encoded_user}.smugmug.com/"
    show_url = f"https://{encoded_user}.smugmug.com/"

    def process(response) -> Result:
        status = response.status_code
        html_doc = response.text

        if status in (404, 410) or '"notFound":true' in html_doc:
            return Result.available(url=show_url)

        if status == 200:
            extra: dict[str, str] = {}
            media: dict[str, str] = {}

            og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html_doc)
            if og_title:
                t = html.unescape(og_title.group(1)).strip()
                if t and t != "SmugMug":
                    extra["title"] = t

            og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', html_doc)
            if og_desc:
                d = html.unescape(og_desc.group(1)).strip()
                if d and d != "Powered by SmugMug":
                    extra["description"] = d

            og_img = re.search(r'<meta property="og:image" content="([^"]+)"', html_doc)
            if og_img:
                media["avatar"] = og_img.group(1).strip()

            return Result.taken(url=show_url, extra=extra, media=media)

        return Result.error(f"Unexpected response status {status}", url=show_url)

    return impersonate_validate(
        url,
        process,
        show_url=show_url,
        allow_redirects=True,
    )
