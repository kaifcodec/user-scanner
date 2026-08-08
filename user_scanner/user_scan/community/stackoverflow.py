import re
from html import unescape
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_stackoverflow(user: str) -> Result:
    url = f"https://stackoverflow.com/users/filter?search={quote(user)}"
    show_url = url

    def process(response):
        text = response.text

        # The endpoint answers with an HTML fragment; without this anchor the
        # body is a challenge or error page and carries no verdict.
        if response.status_code == 200 and 'id="user-browser"' in text:
            if "No users matched your search." in text:
                return Result.available()

            # Split HTML by card indicator to parse each user card block
            cards = re.split(r'<div class="grid--item user-info', text)
            found_card = None

            for card in cards[1:]:
                link_match = re.search(r'<a href="(/users/(\d+)/([^"/]+))"[^>]*>([^<]+)</a>', card)
                if link_match:
                    full_path, uid, slug, name = link_match.groups()
                    if slug.lower() == user.lower() or name.strip().lower() == user.lower():
                        found_card = card
                        break

            if found_card:
                extra = {}
                media = {}
                try:
                    loc_match = re.search(r'<span class="user-location">([^<]*)</span>', found_card)
                    rep_match = re.search(r'title="[^"]*total reputation:\s*([^"]+)"', found_card)
                    img_match = re.search(r'<img src="([^"]+)"', found_card)

                    if loc_match and loc_match.group(1).strip():
                        extra["location"] = unescape(loc_match.group(1).strip())
                    if rep_match:
                        extra["reputation"] = unescape(rep_match.group(1).strip())
                    if img_match:
                        avatar_url = unescape(img_match.group(1).strip())
                        if avatar_url.startswith("//"):
                            avatar_url = "https:" + avatar_url
                        media["avatar"] = avatar_url
                except Exception:
                    pass
                return Result.taken(extra=extra, media=media)

            return Result.available()

        return Result.error(f"Unexpected response body (HTTP {response.status_code})")

    return impersonate_validate(url, process, show_url=show_url)
