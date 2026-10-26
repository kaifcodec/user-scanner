import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_slideshare(user: str) -> Result:
    url = f"https://slideshare.net/{user}"
    show_url = f"https://slideshare.net/{user}?tab=about"

    def process(response):
        html = response.text

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        if '"user":null' in html and '"blankProfile":true' in html:
            return Result.available()

        match = re.search(r'"user":(\{.*?\}),"countryCodeFromFastly"', html)
        if not match:
            if "Client Challenge" in html:
                return Result.error("Blocked by SlideShare challenge page")
            return Result.error("SlideShare profile markers were missing")

        try:
            data = json.loads(match.group(1))
        except ValueError:
            return Result.error("Could not parse SlideShare profile data")

        if str(data.get("login", "")).lower() != user.lower():
            return Result.error("SlideShare profile marker did not match target")

        extra = {}
        media = {}

        if data.get("name"):
            extra["fullname"] = str(data["name"]).strip()
        if data.get("slideshowCount") is not None:
            extra["uploads"] = str(data["slideshowCount"])
        if data.get("followersCount") is not None:
            extra["followers"] = str(data["followersCount"])
        if data.get("followingCount") is not None:
            extra["following"] = str(data["followingCount"])
        if data.get("occupation"):
            extra["occupation"] = str(data["occupation"]).strip()
        if data.get("organization"):
            extra["organization"] = str(data["organization"]).strip()
        if data.get("url"):
            extra["website"] = str(data["url"]).strip()
        if data.get("suspended"):
            extra["suspended"] = True

        location = ", ".join(
            part for part in (data.get("city"), data.get("country")) if part
        ).strip()
        if location:
            extra["location"] = location

        more_info = data.get("moreInfo") or {}
        if more_info.get("twitterHandle"):
            extra["twitter"] = str(more_info["twitterHandle"]).strip()

        if data.get("description"):
            extra["bio"] = str(data["description"]).strip()

        if data.get("photo"):
            media["avatar"] = str(data["photo"]).strip()

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(
        url,
        process,
        warmup_url="https://slideshare.net/",
        show_url=show_url,
        params={"tab": "about"},
        allow_redirects=True,
    )
