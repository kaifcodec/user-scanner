import html
import json
import re
from urllib.parse import quote, urlparse, parse_qs

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_patreon(user: str) -> Result:
    encoded_user = quote(user, safe="")
    url = f"https://www.patreon.com/{encoded_user}"
    show_url = f"https://www.patreon.com/{encoded_user}"

    def process(response) -> Result:
        page = response.text

        if response.status_code == 404 or "Not found | Patreon" in page:
            return Result.available(url=show_url)

        if response.status_code == 200:
            extra: dict[str, str | int] = {}
            media: dict[str, str] = {}

            # Parse schema.org / JSON-LD if present
            ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
            if ld:
                try:
                    data = json.loads(ld.group(1))
                    if isinstance(data, list):
                        data = data[0]
                    if data.get("@type") in ("Person", "Organization") and data.get("name") not in ("Patreon", None):
                        extra["name"] = str(data["name"])
                    if curl := data.get("url"):
                        extra["url"] = str(curl)
                except Exception:
                    pass

            # Extract from OpenGraph metadata
            og_title = re.search(r'<meta property="og:title" content="([^"]+)"', page)
            if og_title:
                t_val = html.unescape(og_title.group(1)).strip()
                if t_val and t_val != "Patreon" and "name" not in extra:
                    cleaned_name = t_val.split(" — ")[0].replace(" | Patreon", "").strip()
                    if cleaned_name:
                        extra["name"] = cleaned_name

            og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', page)
            if og_desc:
                d_val = html.unescape(og_desc.group(1)).strip()
                if d_val and not d_val.startswith("Patreon is empowering"):
                    extra["bio"] = d_val

            og_img = re.search(r'<meta property="og:image" content="([^"]+)"', page)
            if og_img:
                img_val = og_img.group(1).strip()
                if "downloads_logomark" not in img_val:
                    media["avatar"] = img_val

            # Extract user ID from query param u=... if redirected
            parsed = urlparse(response.url)
            qs = parse_qs(parsed.query)
            if "u" in qs and qs["u"]:
                extra["id"] = qs["u"][0]

            return Result.taken(extra=extra, media=media, url=show_url)

        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)
