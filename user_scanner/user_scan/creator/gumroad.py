import html
import json
import re
from typing import cast

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

NOT_FOUND = "<title>Page not found (404) - Gumroad</title>"


def _links(value):
    if isinstance(value, dict):
        if isinstance(value.get("href"), str):
            yield value["href"]
        for item in value.values():
            yield from _links(item)
    elif isinstance(value, list):
        for item in value:
            yield from _links(item)


def validate_gumroad(user: str) -> Result:
    username = user.lower()
    if not re.fullmatch(r"(?=.*[a-z])[a-z0-9]{3,20}", username):
        return Result.error(
            "Username must be 3-20 lowercase letters and numbers, with at least one letter",
            url="https://gumroad.com",
        )

    url = f"https://{username}.gumroad.com/"

    def process(response) -> Result:
        if response.status_code == 404 and NOT_FOUND in response.text:
            return Result.available()

        match = re.search(r'<div id="app" data-page="([^"]+)"', response.text)
        if response.status_code != 200 or not match:
            return Result.error(f"Unexpected Gumroad response: {response.status_code}")

        try:
            page = json.loads(html.unescape(match.group(1)))
        except json.JSONDecodeError:
            return Result.error("Invalid Gumroad profile data")

        props = page.get("props", {})
        profile = props.get("creator_profile")
        if (
            not isinstance(profile, dict)
            or profile.get("subdomain") != f"{username}.gumroad.com"
        ):
            return Result.error("Gumroad profile did not match the requested username")

        reputation = profile.get("reputation") or {}
        preview = next(
            (
                tag.get("content")
                for tag in props.get("_inertia_meta", [])
                if tag.get("property") == "og:image"
            ),
            None,
        )
        links = list(
            dict.fromkeys(
                _links(
                    [
                        section.get("text")
                        for section in props.get("sections", [])
                        if section.get("type") == "SellerProfileRichTextSection"
                    ]
                )
            )
        )
        result = Result.taken(
            extra={
                "uid": profile.get("external_id"),
                "name": profile.get("name"),
                "bio": props.get("bio"),
                "twitter_handle": profile.get("twitter_handle"),
                "verified": profile.get("is_verified"),
                "rating": reputation.get("average"),
                "reviews": reputation.get("count"),
                "products": reputation.get("products_count"),
            },
            media={"avatar": profile.get("avatar_url"), "preview": preview},
        )
        if links:
            cast(dict, result.extra)["links"] = links
        return result

    return generic_validate(url, process, show_url=url, follow_redirects=True)
