import json
import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.flickr.com"

# Public-profile fields naming the owner's account on another platform. Flickr
# stores the bare handle and derives the sibling `<field>Url` from it, so the
# handle is what gets emitted.
SOCIAL_FIELDS = ("facebook", "instagram", "pinterest", "tumblr", "twitter")


def validate_flickr(user: str) -> Result:
    url = f"{BASE_URL}/photos/{user}"

    def process(r):
        owner, profile, contacts = _models(r.text)

        if r.status_code == 404:
            if owner:
                return Result.error("404 response carrying a photostream owner")
            return Result.available()

        if r.status_code != 200:
            return Result.error(f"HTTP {r.status_code}")

        # /photos/tags, /photos/search and friends answer 200 with a page that
        # has no owner, and every real photostream names its own handle.
        if not _owns(owner, user):
            return Result.error("200 response with no matching photostream owner")

        extra, media = _extract(owner, profile, contacts)
        if nsid := owner.get("id"):
            extra.update(_public_profile(str(nsid)))
        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, allow_redirects=True)


def _main_models(text: str) -> dict:
    match = re.search(r"modelExport:\s*(.*?),\s*auth", text)
    if not match:
        return {}

    try:
        data = json.loads(urllib.parse.unquote(match.group(1)))
    except (json.JSONDecodeError, ValueError):
        return {}

    return data.get("main") or {}


def _models(text: str) -> tuple[dict, dict, dict]:
    main = _main_models(text)

    def first(key: str) -> dict:
        models = main.get(key) or [{}]
        return models[0].get("data") or {}

    photostream = first("photostream-models")
    owner = (photostream.get("owner") or {}).get("data") or photostream.get("owner") or {}
    return owner, first("person-profile-models"), first("person-contacts-count-models")


def _owns(owner: dict, user: str) -> bool:
    # Handles resolve case-insensitively, and accounts with no custom URL are
    # addressed by their NSID (`12345678@N00`) instead of a path alias.
    candidates = {str(owner.get("pathAlias") or ""), str(owner.get("id") or "")}
    return user.lower() in {c.lower() for c in candidates if c}


def _extract(owner: dict, profile: dict, contacts: dict) -> tuple[dict, dict]:
    extra: dict = {}
    media: dict = {}

    if username := owner.get("username"):
        extra["display_name"] = username
    if realname := owner.get("realname"):
        extra["fullname"] = realname
    if nsid := owner.get("id"):
        extra["user_id"] = nsid
    if path_alias := owner.get("pathAlias"):
        extra["path_alias"] = path_alias
    if location := profile.get("location"):
        extra["location"] = location
    if profile.get("photoCount") is not None:
        extra["photos"] = int(profile["photoCount"])
    if contacts.get("followerCount") is not None:
        extra["followers"] = int(contacts["followerCount"])
    if contacts.get("followingCount") is not None:
        extra["following"] = int(contacts["followingCount"])

    buddyicon = owner.get("buddyicon") or {}
    avatar = (buddyicon.get("data") or {}).get("retina") or buddyicon.get("retina")
    if avatar:
        media["avatar"] = f"https:{avatar}" if avatar.startswith("//") else avatar

    return extra, media


def _public_profile(nsid: str) -> dict:
    """The accounts the profile links elsewhere, which only the /people/ page
    carries — the photostream omits them. Addressed by NSID so the lookup is
    immune to the handle's casing. Best-effort: a failure just yields no extra."""
    try:
        response = impersonate_request(f"{BASE_URL}/people/{nsid}/", allow_redirects=True)
        if response.status_code != 200:
            return {}
        profile = _public_profile_object(response.text, nsid)
    except Exception:
        return {}

    extra = {field: profile[field] for field in SOCIAL_FIELDS if profile.get(field)}
    if occupation := profile.get("occupation"):
        extra["occupation"] = occupation
    return extra


def _public_profile_object(text: str, nsid: str) -> dict:
    """The public-profile model belonging to the NSID asked for. The /people/
    page embeds a person model per contact, so the object is matched on the
    owner's id rather than taken by position."""
    for entry in _main_models(text).get("person-public-profile-models") or []:
        data = (entry or {}).get("data")
        if isinstance(data, dict) and str(data.get("id") or "") == nsid:
            return data
    return {}
