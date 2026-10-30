import html
import json
import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_crevado(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://{encoded_user}.crevado.com"
    show_url = f"https://{encoded_user}.crevado.com"

    def process(response) -> Result:
        status = response.status_code
        html_doc = response.text

        if status in (404, 410) or "site not found" in html_doc.lower():
            return Result.available(url=show_url)

        if status == 200:
            extra: dict[str, str] = {}
            media: dict[str, str] = {}

            # Parse JSON-LD Person if present
            ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_doc, re.DOTALL)
            if ld:
                try:
                    data = json.loads(ld.group(1))
                    if isinstance(data, dict) and data.get("name"):
                        extra["name"] = str(data["name"])
                except Exception:
                    pass

            og_title = re.search(r'<meta content="([^"]+)" property="og:title"', html_doc)
            if not og_title:
                og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html_doc)
            if og_title:
                t = html.unescape(og_title.group(1)).strip()
                if t and "Portfolio" in t:
                    extra["title"] = t
                    if "name" not in extra and " - " in t:
                        extra["name"] = t.split(" - ")[-1].replace("'s Portfolio", "").strip()

            og_img = re.search(r'<meta content="([^"]+)" property="og:image"', html_doc)
            if not og_img:
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
