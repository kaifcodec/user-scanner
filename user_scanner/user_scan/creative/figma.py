import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_figma(user: str) -> Result:
    show_url = f"https://www.figma.com/@{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            html = response.text
            extra: dict[str, object] = {}
            media: dict[str, str] = {}

            # Parse schema.org ld+json for rich profile data
            ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            if ld:
                try:
                    data = json.loads(ld.group(1))
                    for item in data.get("@graph", []):
                        entity = item.get("mainEntity")
                        if entity and isinstance(entity, dict):
                            if entity.get("name"):
                                extra["name"] = entity["name"]
                            if entity.get("description"):
                                extra["bio"] = entity["description"]
                            if entity.get("image"):
                                media["avatar"] = entity["image"]
                            if entity.get("sameAs"):
                                extra["website"] = (
                                    entity["sameAs"][0]
                                    if isinstance(entity["sameAs"], list)
                                    else str(entity["sameAs"])
                                )
                except Exception:
                    pass

            if "name" not in extra:
                match = re.search(r'<meta\s+(?:name|property)="twitter:title"\s+content="([^"]+)"', html)
                if match:
                    title_content = match.group(1)
                    if " · @" in title_content:
                        extra["name"] = title_content.split(" · @")[0].strip()
                    elif "(@" in title_content:
                        extra["name"] = title_content.split("(@")[0].strip()
                    else:
                        extra["name"] = title_content

            if "bio" not in extra:
                desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
                if desc_match:
                    extra["bio"] = desc_match.group(1).strip()

            if "avatar" not in media:
                img_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
                if img_match and "default" not in img_match.group(1):
                    media["avatar"] = img_match.group(1).replace("&#47;", "/")

            return Result.taken(url=show_url, extra=extra, media=media if media else None)

        elif response.status_code == 404:
            return Result.available(url=show_url)
        elif response.status_code == 202:
            return Result.error("Access blocked by Figma AWS WAF challenge (202)", url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(show_url, process, show_url=show_url, allow_redirects=True)

