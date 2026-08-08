import json
import re

from user_scanner.core.orchestrator import Result, generic_validate

# Served instead of an avatar when the creator uploaded none.
PLACEHOLDER_AVATAR = "/img/Icon_BentBox"


def validate_bentbox(user):
    url = f"https://bentbox.co/{user}"
    show_url = url

    def process(response):
        html = response.text

        person = _profile_person(html)
        if person:
            return Result.taken(extra=_extra(person, html), media=_media(html), url=show_url)

        if "User not found" in html:
            return Result.available(url=show_url)

        # Reserved routes (/login, /explore) and whitespace normalisation both
        # redirect. Redirects are not followed, so the body carries no verdict.
        if 300 <= response.status_code < 400:
            target = response.headers.get("location") or "an unnamed target"
            return Result.error(
                f"Redirected to {target}; the response carries no verdict", url=show_url
            )

        if response.status_code in (403, 429):
            return Result.error(
                f"Rate limit / bot protection block (HTTP {response.status_code}). "
                "Retry with a proxy or lower concurrency.",
                url=show_url,
            )

        return Result.error(
            f"Neither a profile nor the not-found marker (HTTP {response.status_code})",
            url=show_url,
        )

    return generic_validate(url, process, show_url=show_url)


def _profile_person(html: str) -> dict:
    """The Person node of the ProfilePage JSON-LD, which only real profiles carry."""
    for block in re.findall(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.DOTALL):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if data.get("@type") != "ProfilePage":
            continue
        person = data.get("mainEntity")
        if isinstance(person, dict):
            return person
    return {}


def _extra(person: dict, html: str) -> dict:
    # og:title, og:url, profile:username and alternateName all echo the casing
    # from the request, so only these server-derived values are trustworthy.
    extra = {
        "fullname": (person.get("name") or "").strip(),
        "profile_id": person.get("identifier"),
    }

    bio = re.search(r'<p class="fs-lg mb-0"[^>]*>(.*?)</p>', html, re.DOTALL)
    if bio:
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", bio.group(1))).strip()
        if text:
            extra["bio"] = text

    for counter in person.get("interactionStatistic") or []:
        if counter.get("interactionType", "").endswith("/FollowAction"):
            extra["followers"] = counter.get("userInteractionCount")

    for value, label in re.findall(
        r'<span class="stat-value">(\d+)</span>\s*<span class="stat-label">(\w+)</span>', html
    ):
        extra[label.lower()] = value

    return extra


def _media(html: str) -> dict:
    avatar = re.search(r'property="og:image" content="([^"]+)"', html)
    if not avatar or PLACEHOLDER_AVATAR in avatar.group(1):
        return {}
    return {"avatar": avatar.group(1)}
