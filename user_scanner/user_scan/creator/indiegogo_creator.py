import json
from urllib.parse import quote

from user_scanner.core.orchestrator import Result, generic_validate

_SOCIAL_FIELDS = {
    0: "facebook",
    1: "twitter",
    2: "youtube",
    3: "instagram",
    4: "social_website",
}


def validate_indiegogo_creator(user: str) -> Result:
    url = f"https://www.indiegogo.com/en/creators/{quote(user, safe='')}"

    def process(response):
        body = response.text
        if response.status_code == 404 and "<title>404: Page Not Found - Indiegogo</title>" in body:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        props = _props(body)
        if not props or str(props.get("urlName", "")).casefold() != user.casefold():
            return Result.error("200 without the matching Indiegogo account data")

        extra = {
            "id": props.get("creatorID"),
            "name": props.get("name"),
            "bio": props.get("description"),
            "location": props.get("displayedLocation"),
            "website": props.get("websiteUrl"),
        }
        for social in props.get("socialMediaUrls") or []:
            if isinstance(social, dict) and (field := _SOCIAL_FIELDS.get(social.get("type"))):
                extra[field] = social.get("url")

        media = {"avatar": props.get("creatorImageUrl")}
        if props.get("bannerImages"):
            media["banner"] = props["bannerImages"][0]
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url)


def _props(body: str) -> dict | None:
    marker = "'App.Views.CreatorView', App.Views.CreatorView, "
    start = body.find(marker)
    if start == -1:
        return None

    start = body.find('{"props":', start)
    end = body.find(");</script>", start)
    if start == -1 or end == -1:
        return None

    props = json.loads(body[start:end]).get("props")
    return props if isinstance(props, dict) else None
