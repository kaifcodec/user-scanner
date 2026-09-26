import json
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

USER_DATA_MARKER = "globalData.user = "


def validate_inkitt(user: str) -> Result:
    url = f"https://www.inkitt.com/{quote(user, safe='')}"

    def process(response) -> Result:
        try:
            start = response.text.index(USER_DATA_MARKER) + len(USER_DATA_MARKER)
            profile, _ = json.JSONDecoder().raw_decode(response.text[start:])
        except (ValueError, TypeError):
            return Result.error("Inkitt profile data was missing")

        if response.status_code == 404:
            if (
                profile == {}
                and 'controller: "errors"' in response.text
                and 'action: "not_found"' in response.text
            ):
                return Result.available()
            return Result.error("Unexpected Inkitt not-found response")

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        if (
            not isinstance(profile, dict)
            or not profile.get("id")
            or str(profile.get("username", "")).casefold() != user.casefold()
        ):
            return Result.error("Inkitt profile markers were missing")

        galatea = profile.get("user_galatea_settings")
        galatea = galatea if isinstance(galatea, dict) else {}
        settings = profile.get("user_settings")
        settings = settings if isinstance(settings, dict) else {}
        featured_tier = profile.get("featured_patron_tier_settings")
        featured_tier = featured_tier if isinstance(featured_tier, dict) else {}
        patron_tiers = profile.get("patron_tiers")
        patron_tiers = patron_tiers if isinstance(patron_tiers, list) else []

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
            "patron_wall_posts": profile.get("patron_wall_posts_count"),
            "verified": profile.get("is_verified"),
            "vip": profile.get("is_vip"),
            "staff": profile.get("is_staff"),
            "shadow_banned": profile.get("shadow_banned"),
            "email": profile.get("public_email"),
            "website": profile.get("homepage_url"),
            "donate_url": profile.get("donate_url"),
            "facebook": profile.get("facebook_url"),
            "twitter": profile.get("twitter_url"),
            "instagram": profile.get("instagram_url"),
            "direct_messages_enabled": profile.get("direct_messaging_setting"),
            "wall_post_setting": profile.get("wall_post_setting"),
            "preferred_languages": settings.get("preferred_search_languages") or None,
            "patron_program": profile.get("memberOfPatronProgram"),
            "patron_tiers": [
                {key: value for key, value in tier.items() if key != "image"}
                for tier in patron_tiers
                if isinstance(tier, dict)
            ]
            or None,
            "featured_patron_tier_id": featured_tier.get("patron_tier_id"),
            "featured_patron_tier_most_popular": featured_tier.get("most_popular"),
            "galatea_author_id": galatea.get("galatea_author_id"),
            "galatea_username": galatea.get("galatea_username"),
            "galatea_promo_link": galatea.get("promo_link"),
            "galatea_wall_enabled": galatea.get("galatea_wall_enabled"),
        }
        media = {
            "avatar": profile.get("large_profile_picture_url"),
            "cover": profile.get("cover_picture_url"),
        }
        media.update(
            {
                f"patron_tier_{tier.get('id', index)}": tier["image"]
                for index, tier in enumerate(patron_tiers, 1)
                if isinstance(tier, dict) and tier.get("image")
            }
        )
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url, follow_redirects=True)
