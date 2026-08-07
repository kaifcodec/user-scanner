import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://kick.com"

SOCIALS = ("twitter", "instagram", "youtube", "tiktok", "facebook", "discord")


def validate_kick(user: str) -> Result:
    show_url = f"{BASE_URL}/{user}"

    def process(response):
        if response.status_code == 404:
            if '"message":"Channel not found."' in response.text:
                return Result.available()
            return Result.error("Unexpected 404 (not the not-found payload)")

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        try:
            channel = json.loads(response.text)
        except json.JSONDecodeError:
            return Result.error("Channel API returned a non-JSON body")

        slug = channel.get("slug")
        if not isinstance(slug, str) or slug.lower() != user.lower():
            return Result.error("Channel payload did not match the requested handle")

        return Result.taken(extra=_profile(channel), media=_media(channel))

    # kick.com/<user> is a client-rendered shell that answers 200 for any handle,
    # so the channel API is the only source of a verdict.
    return impersonate_validate(
        f"{BASE_URL}/api/v2/channels/{user}", process, show_url=show_url
    )


def _profile(channel: dict) -> dict:
    account = channel.get("user") or {}
    livestream = channel.get("livestream") or {}

    extra = {
        "display_name": account.get("username"),
        "user_id": account.get("id"),
        "channel_id": channel.get("id"),
        "bio": _clean(account.get("bio")),
        "verified": channel.get("verified"),
        "followers": _as_int(channel.get("followers_count")),
        "is_banned": channel.get("is_banned"),
        "is_affiliate": channel.get("is_affiliate"),
        "subscriptions_enabled": channel.get("subscription_enabled"),
        "vod_enabled": channel.get("vod_enabled"),
        "is_live": bool(livestream.get("is_live")),
    }

    extra.update({name: account.get(name) for name in SOCIALS})

    recent = [c.get("name") for c in channel.get("recent_categories") or []]
    extra["recent_categories"] = ", ".join(x for x in recent if x)

    if livestream:
        categories = [c.get("name") for c in livestream.get("categories") or []]
        extra.update(
            {
                "stream_title": _clean(livestream.get("session_title")),
                "stream_category": ", ".join(x for x in categories if x),
                "stream_viewers": livestream.get("viewer_count"),
                "stream_started_at": livestream.get("start_time"),
                "stream_language": livestream.get("language"),
                "stream_is_mature": livestream.get("is_mature"),
            }
        )

    return {key: value for key, value in extra.items() if value not in (None, "")}


def _media(channel: dict) -> dict:
    account = channel.get("user") or {}
    livestream = channel.get("livestream") or {}

    media = {
        "avatar": account.get("profile_pic"),
        "banner": (channel.get("banner_image") or {}).get("url"),
        "offline_banner": (channel.get("offline_banner_image") or {}).get("src"),
        "stream_thumbnail": (livestream.get("thumbnail") or {}).get("url"),
    }
    return {key: value for key, value in media.items() if value}


def _as_int(value) -> int | None:
    # followers_count arrives as an int on some channels and a numeric string on others.
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean(value) -> str | None:
    if not isinstance(value, str):
        return None
    return re.sub(r"\s+", " ", value).strip()
