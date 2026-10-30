import json
import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_buymeacoffee(user: str) -> Result:
    encoded_user = quote(user, safe="")
    url = f"https://buymeacoffee.com/{encoded_user}"
    show_url = f"https://buymeacoffee.com/{encoded_user}"

    def process(response) -> Result:
        html = response.text

        if response.status_code == 404 or "Not found | Buy Me a Coffee" in html:
            return Result.available(url=show_url)

        if response.status_code == 200:
            extra: dict[str, str | int | bool] = {}
            media: dict[str, str] = {}

            # Inertia.js data extraction
            match = re.search(r'<script\b[^>]*\bdata-page="app"[^>]*>(.*?)</script>', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if data.get("component") == "Error" and data.get("props", {}).get("status") == 404:
                        return Result.available(url=show_url)

                    cdata = data.get("props", {}).get("creator_data", {}).get("data", {})
                    slug = cdata.get("slug")
                    if isinstance(slug, str) and slug.lower() == user.lower():
                        if name := cdata.get("name"):
                            extra["name"] = str(name).strip()
                        if user_id := cdata.get("user_id"):
                            extra["id"] = user_id
                        if bio := (cdata.get("work") or cdata.get("description")):
                            clean_bio = re.sub(r"<[^>]+>", " ", str(bio)).strip()
                            if clean_bio:
                                extra["bio"] = clean_bio
                        if currency := cdata.get("currency"):
                            extra["currency"] = str(currency)
                        if (price := cdata.get("coffee_price")) is not None:
                            extra["coffee_price"] = str(price)
                        if twitter := cdata.get("twitter_handle"):
                            extra["twitter"] = str(twitter)
                        if (posts := cdata.get("published_post_count")) is not None:
                            extra["published_posts"] = posts
                        if (membership := cdata.get("membership_enabled")) is not None:
                            extra["membership_enabled"] = membership
                        if dp := cdata.get("dp"):
                            media["avatar"] = str(dp)

                        return Result.taken(extra=extra, media=media, url=show_url)
                except Exception:
                    pass

            # Fallback to metadata regex if Inertia parsing failed
            n = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if not n:
                n = re.search(r"<title[^>]*>([^<]+?)(?:\s*-\s*Buymeacoffee)?</title>", html, re.IGNORECASE)
            if n and "Not found" not in n.group(1):
                extra["name"] = n.group(1).strip()

            m = re.search(r'<meta name="description" content="([^"]+)"', html)
            if not m:
                m = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if m:
                extra["bio"] = m.group(1).strip()

            img = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            if img:
                media["avatar"] = img.group(1)

            if extra or media:
                return Result.taken(extra=extra, media=media, url=show_url)

        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)
