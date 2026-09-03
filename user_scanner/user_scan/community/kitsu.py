import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_kitsu(user: str) -> Result:
    url = "https://kitsu.app/api/edge/users"
    encoded_user = urllib.parse.quote(user)
    show_url = f"https://kitsu.app/users/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/vnd.api+json",
    }
    params = {"filter[name]": user}

    def process(response) -> Result:
        if response.status_code == 200:
            try:
                data = response.json()
                data_list = data.get("data")
                if isinstance(data_list, list):
                    if len(data_list) == 0:
                        return Result.available(url=show_url)

                    for item in data_list:
                        attrs = item.get("attributes", {})
                        uname = attrs.get("name", "")
                        if uname.lower() == user.lower():
                            extra: dict[str, str] = {}
                            media: dict[str, str] = {}

                            if attrs.get("name"):
                                extra["name"] = str(attrs["name"])
                            if attrs.get("about"):
                                extra["about"] = str(attrs["about"])
                            if attrs.get("location"):
                                extra["location"] = str(attrs["location"])
                            if attrs.get("waifuOrHusbando"):
                                extra["waifu_husbando"] = str(attrs["waifuOrHusbando"])
                            if attrs.get("followersCount") is not None:
                                extra["followers"] = str(attrs["followersCount"])
                            if attrs.get("followingCount") is not None:
                                extra["following"] = str(attrs["followingCount"])
                            if attrs.get("createdAt"):
                                extra["joined"] = str(attrs["createdAt"])

                            avatar_obj = attrs.get("avatar")
                            if isinstance(avatar_obj, dict):
                                avatar_url = avatar_obj.get("original") or avatar_obj.get("medium")
                                if avatar_url:
                                    media["avatar"] = str(avatar_url)

                            return Result.taken(url=show_url, extra=extra, media=media)

                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("Kitsu 200 response missing valid user payload")

        if response.status_code == 404:
            return Result.available(url=show_url)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, params=params, follow_redirects=True)
