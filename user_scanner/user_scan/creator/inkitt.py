import json
import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import iter_next_app_flight_chunks
from user_scanner.core.result import Result


def validate_inkitt(user: str) -> Result:
    url = f"https://www.inkitt.com/{quote(user, safe='')}"

    def process(response) -> Result:
        if response.status_code == 404:
            if "__next_error__" in response.text or "not-found" in response.text:
                return Result.available()
            return Result.error("Unexpected Inkitt not-found response")

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        profile = None
        for chunk in iter_next_app_flight_chunks(response.text):
            if '"user":{' not in chunk:
                continue
            m = re.search(r'"user":(\{(?:[^{}]|(?:\{[^{}]*\}))*\})', chunk)
            if m:
                try:
                    data = json.loads(m.group(1))
                    if isinstance(data, dict) and data.get("username"):
                        profile = data
                        break
                except Exception:
                    pass

        if not profile:
            return Result.error("Inkitt profile data was missing")

        if str(profile.get("username", "")).casefold() != user.casefold():
            return Result.error("Inkitt profile markers were missing")

        extra = {
            "id": profile.get("id"),
            "name": profile.get("name"),
            "bio": profile.get("description"),
            "about": profile.get("about"),
            "city": profile.get("city"),
            "followers": profile.get("followers_count"),
            "following": profile.get("followings_count"),
            "stories": profile.get("published_stories_count"),
            "wall_posts": profile.get("wall_posts_count"),
            "galatea_wall_posts": profile.get("galatea_wall_posts_count"),
            "verified": profile.get("is_verified"),
            "vip": profile.get("is_vip"),
            "staff": profile.get("is_staff"),
            "email": profile.get("public_email"),
            "website": profile.get("homepage_url"),
            "donate_url": profile.get("donate_url"),
            "facebook": profile.get("facebook_url"),
            "twitter": profile.get("twitter_url"),
            "instagram": profile.get("instagram_url"),
        }

        media = {
            "avatar": profile.get("large_profile_picture_url"),
            "cover": profile.get("cover_picture_url"),
        }

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, show_url=url)
