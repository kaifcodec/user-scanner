from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_bugcrowd(user: str) -> Result:
    encoded = quote(user, safe="")
    api_url = f"https://bugcrowd.com/profile-service/v1/profiles/{encoded}"
    show_url = f"https://bugcrowd.com/h/{encoded}"

    def process(response):
        data = response.json()

        if response.status_code == 404 and data.get("error") == "Not Found":
            return Result.available()

        if response.status_code == 404 and not data:
            return Result.taken(extra={"public": False})

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        username = data.get("username")
        if not isinstance(username, str) or username.casefold() != user.casefold():
            return Result.error("Profile response did not match the requested username")

        extra = {
            "public": True,
            "country": data.get("countryCode"),
            "twitter": data.get("twitterUsername"),
            "linkedin": data.get("linkedinUrl"),
            "website": data.get("website"),
            "bio": data.get("biography"),
            "verified": data.get("identityVerified"),
        }
        media = {
            "avatar": data.get("avatarUrl"),
            "banner": data.get("bannerImageUrl"),
        }
        return Result.taken(extra=extra, media=media)

    return generic_validate(
        api_url,
        process,
        show_url=show_url,
    )
