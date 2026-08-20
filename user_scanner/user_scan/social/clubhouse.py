from urllib.parse import quote

from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_clubhouse(user: str) -> Result:
    encoded = quote(user, safe="")
    url = f"https://www.clubhouse.com/@{encoded}"

    def process(response):
        if response.status_code == 404 and response.text.strip() == "404":
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        data = parse_next_pages_data(response.text)
        if data is None:
            return Result.error("Missing or invalid Clubhouse profile data")

        try:
            page_props = data["props"]["pageProps"]
            profile = page_props["routeProps"]["user"]
        except (KeyError, TypeError):
            return Result.error("Invalid Clubhouse profile data")

        username = profile.get("username")
        if not isinstance(username, str) or username.casefold() != user.casefold():
            return Result.error("Profile response did not match the requested username")

        route = page_props["routeProps"]
        extra = {
            key: value
            for key, value in {
                "fullname": profile.get("full_name"),
                "bio": profile.get("bio"),
                "twitter": profile.get("twitter_username"),
                "instagram": profile.get("instagram_username"),
                "followers": route.get("num_followers"),
                "following": route.get("num_following"),
                "friends": route.get("friend_count"),
            }.items()
            if value not in (None, "")
        }
        avatar = profile.get("photo_url")
        return Result.taken(extra=extra, media={"avatar": avatar} if avatar else {})

    return generic_validate(url, process, show_url=url, follow_redirects=True)
