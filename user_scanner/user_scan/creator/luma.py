from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.result import Result


def validate_luma(user: str) -> Result:
    encoded_user = quote(user, safe="")
    url = f"https://luma.com/user/{encoded_user}"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}", url=url)

        data = parse_next_pages_data(response.text)
        if not data or data.get("page") != "/user/[...username]":
            return Result.error("Luma profile data was missing", url=url)

        page_props = data.get("props", {}).get("pageProps", {})
        initial_data = page_props.get("initialData")

        if page_props.get("status") == 404 and initial_data is None:
            return Result.available(url=url)

        if page_props.get("code") == "user-suspended" or (page_props.get("status") == 400 and "errorInfo" in page_props):
            return Result.taken(extra={"status": "suspended"}, url=url)

        if not isinstance(initial_data, dict):
            return Result.error("Unexpected Luma profile data", url=url)

        profile = initial_data.get("user")
        username = profile.get("username") if isinstance(profile, dict) else None
        if not isinstance(username, str) or username.casefold() != user.casefold():
            return Result.error("Luma profile did not match the requested username", url=url)

        extra = {
            "uid": profile.get("api_id"),
            "display_name": profile.get("name"),
            "first_name": profile.get("first_name"),
            "last_name": profile.get("last_name"),
            "bio": profile.get("bio_short"),
            "verified": profile.get("is_verified"),
            "timezone": profile.get("timezone"),
            "joined_at": initial_data.get("joined_at"),
            "events_hosted": initial_data.get("event_hosted_count"),
            "events_attended": initial_data.get("event_attended_count"),
            "events_together": initial_data.get("event_together_count"),
            "website": profile.get("website"),
            "instagram_handle": profile.get("instagram_handle"),
            "linkedin_handle": profile.get("linkedin_handle"),
            "tiktok_handle": profile.get("tiktok_handle"),
            "twitter_handle": profile.get("twitter_handle"),
            "youtube_handle": profile.get("youtube_handle"),
        }
        # Filter out None values
        clean_extra = {k: v for k, v in extra.items() if v is not None}

        media = {}
        if avatar := profile.get("avatar_url"):
            media["avatar"] = str(avatar)

        return Result.taken(extra=clean_extra, media=media, url=url)

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)
