from urllib.parse import quote

from user_scanner.core.orchestrator import Result, generic_validate

API_URL = "https://xpdhqqwgprlqmqaqmnyx.supabase.co/rest/v1/profiles"
# DevHunt's public Supabase anon key expires 2033-05-23 04:14:47 UTC.
API_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwZGhxcXdncHJscW1xYXFtbnl4Iiw"
    "icm9sZSI6ImFub24iLCJpYXQiOjE2ODQ4NTg0ODcsImV4cCI6MjAwMDQzNDQ4N30."
    "fwN6a_NzygrFxhj0GCxGnJJpHv8q8iNEjY1jvhL8Kv0"
)
PROFILE_FIELDS = (
    "id,username,full_name,avatar_url,website_url,headline,about,social_url,"
    "updated_at,"
    "products(name)"
)


def validate_devhunt(user: str) -> Result:
    profile_url = f"https://devhunt.org/@{quote(user, safe='')}"
    api_url = (
        f"{API_URL}?username=eq.{quote(user, safe='')}&select={PROFILE_FIELDS}"
        "&products.deleted=eq.false"
    )

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        profiles = response.json()
        if profiles == []:
            return Result.available()

        profile = profiles[0]
        if profile.get("username") != user:
            return Result.error("Profile did not match the requested username")

        extra = {
            "fullname": profile.get("full_name"),
            "headline": profile.get("headline"),
            "bio": profile.get("about"),
            "website": profile.get("website_url"),
            "social_link": profile.get("social_url"),
            "owner_id": profile.get("id"),
            "updated_at": profile.get("updated_at"),
        }
        launched_tools = [tool["name"] for tool in profile["products"]]

        if launched_tools:
            extra["launched_tools"] = launched_tools

        return Result.taken(
            extra=extra,
            media={"avatar": profile.get("avatar_url")},
        )

    return generic_validate(
        api_url,
        process,
        show_url=profile_url,
        headers={"apikey": API_KEY},
    )
