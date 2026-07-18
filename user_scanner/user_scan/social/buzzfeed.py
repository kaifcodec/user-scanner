import json
import re
from datetime import datetime
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_buzzfeed(user: str) -> Result:
    url = f"https://www.buzzfeed.com/{user}"
    show_url = f"https://www.buzzfeed.com/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            extra = {}
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    page_props = data.get("props", {}).get("pageProps", {})
                    user_data = page_props.get("user", {})

                    if user_data.get("displayName"):
                        extra["display_name"] = user_data.get("displayName")
                    if user_data.get("bio"):
                        extra["bio"] = user_data.get("bio")
                    
                    if user_data.get("image"):
                        img = user_data.get("image")
                        if not img.startswith("http"):
                            img = f"https://img.buzzfeed.com/buzzfeed-static{img}"
                        extra["avatar_url"] = img

                    if user_data.get("memberSince"):
                        try:
                            created_ts = int(user_data.get("memberSince"))
                            extra["joined"] = datetime.utcfromtimestamp(created_ts).strftime("%Y-%m-%d")
                        except Exception:
                            pass

                    if page_props.get("points") is not None:
                        extra["points"] = int(page_props.get("points"))
                    if page_props.get("buzz_count") is not None:
                        extra["posts"] = int(page_props.get("buzz_count"))

                    # Parse social links
                    links = []
                    for s in user_data.get("social", []):
                        if s.get("url"):
                            links.append(s.get("url"))
                    if links:
                        extra["links"] = links

                    return Result.taken(extra=extra)
                except Exception:
                    pass

            return Result.taken()

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
