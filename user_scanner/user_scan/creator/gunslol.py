import json
import re
from base64 import b64decode
from datetime import datetime, timezone
from html import unescape
from urllib.parse import quote

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.helpers import is_valid_email
from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.nextjs import iter_next_app_flight_chunks
from user_scanner.core.result import Result


def _badge_names(badges):
    if not isinstance(badges, list):
        return None
    names = []
    for badge in badges:
        name = badge.get("name") if isinstance(badge, dict) else badge
        if isinstance(name, str) and name:
            names.append(name)
    return names or None


def validate_gunslol(user: str) -> Result:
    encoded_user = quote(user, safe="")
    profile_url = f"https://guns.lol/{encoded_user}"
    api_url = f"https://guns.lol/api/auth/username/{encoded_user}/availability"

    def process(response):
        if response.status_code == 401:
            return Result.error("Blocked by guns.lol bot challenge")
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        try:
            availability = response.json()
        except ValueError:
            return Result.error("Invalid guns.lol availability response")

        match availability:
            case {"available": True}:
                return Result.available()
            case {"available": False, "error": "Username is taken."}:
                pass
            case {"error": error}:
                return Result.error(error)
            case _:
                return Result.error("Unexpected guns.lol availability response")

        extra = {}
        media = {}
        try:
            profile_response = impersonate_request(profile_url, allow_redirects=True)
        except RequestException:
            return Result.taken()

        if profile_response.status_code == 200:
            profile = {}
            for chunk in iter_next_app_flight_chunks(profile_response.text):
                start = chunk.find('{"data":')
                if start < 0 or '"success":true' not in chunk:
                    continue
                try:
                    payload = json.JSONDecoder().raw_decode(chunk[start:])[0]
                except json.JSONDecodeError:
                    continue
                data = payload.get("data")
                if isinstance(data, dict) and data.get("uid") is not None:
                    profile = data
                    break

            config = profile.get("config", {})
            if isinstance(config, dict):
                extra.update(
                    {
                        "name": config.get("display_name"),
                        "bio": config.get("description"),
                        "profile_views": config.get("page_views"),
                        "location": config.get("location"),
                        "badges": _badge_names(config.get("user_badges")),
                        "custom_badges": _badge_names(config.get("custom_badges")),
                    }
                )
                media["avatar"] = config.get("avatar")
                socials = config.get("socials")
                if not isinstance(socials, list):
                    socials = []
                social_links = []
                public_emails = []
                social_handles = {}
                for social in socials:
                    if not isinstance(social, dict):
                        continue
                    value = social.get("value")
                    if not isinstance(value, str):
                        continue
                    if value.startswith(("http://", "https://")):
                        social_links.append(value)
                        continue
                    platform = social.get("social")
                    if platform == "email":
                        try:
                            email = b64decode(value, validate=True).decode().strip()
                        except (ValueError, UnicodeDecodeError):
                            continue
                        if is_valid_email(email) and email not in public_emails:
                            public_emails.append(email)
                    elif isinstance(platform, str) and value:
                        social_handles[platform] = value
                extra.update(
                    {
                        "social_links": social_links or None,
                        "public_email": public_emails or None,
                        "social_handles": social_handles or None,
                    }
                )
            extra.update(
                {
                    "uid": profile.get("uid"),
                    "profile_id": profile.get("_id"),
                    "account_created": (
                        datetime.fromtimestamp(profile["account_created"], timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z")
                    ),
                    "aliases": profile.get("aliases") or None,
                }
            )
            discord = profile.get("discord")
            if isinstance(discord, dict):
                extra.update(
                    {
                        "discord_username": discord.get("username"),
                        "discord_id": discord.get("id"),
                        "discord_badges": _badge_names(discord.get("user_badges")),
                    }
                )
            primary_username = profile.get("username")
            if (
                isinstance(primary_username, str)
                and primary_username.casefold() != user.casefold()
            ):
                extra["primary_username"] = primary_username
            image = re.search(
                r'<meta property="og:image" content="([^"]+)"',
                profile_response.text,
            )
            if image:
                media["image"] = unescape(image.group(1))

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(
        api_url,
        process,
        show_url=profile_url,
        allow_redirects=True,
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
