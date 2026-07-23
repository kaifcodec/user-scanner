import json
import re
from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.cam4.com"

# Scalar profile fields worth surfacing, mapped to friendlier extra keys.
FIELDS = {
    "userId": "user_id",
    "age": "age",
    "gender": "gender",
    "sexPreference": "sex_preference",
    "ethnicity": "ethnicity",
    "maritalStatus": "marital_status",
    "countryId": "country",
    "city": "city",
    "timeZoneId": "timezone",
    "hairColor": "hair_color",
    "hairLength": "hair_length",
    "eyeColor": "eye_color",
    "bodyHair": "body_hair",
    "breastSize": "breast_size",
    "penisSize": "penis_size",
    "online": "online",
    "bio": "bio",
}

# Epoch-millisecond timestamps, surfaced as plain dates.
DATE_FIELDS = {"creationDate": "created_at", "lastBroadcast": "last_broadcast"}


def validate_cam4(user: str) -> Result:
    url = f"{BASE_URL}/rest/v1.0/profile/{user}/info"
    show_url = f"{BASE_URL}/{user}"

    def process(response):
        # The API answers a missing handle with 404 and an empty body; a 404
        # carrying content is an edge/WAF page, not a verdict.
        if response.status_code == 404:
            if not response.text.strip():
                return Result.available(url=show_url)
            return Result.error("Unexpected 404 (body was not empty)", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        try:
            profile = json.loads(response.text)
        except json.JSONDecodeError:
            return Result.error("Profile response was not JSON", url=show_url)

        # Confirm the payload describes the handle we asked for.
        if str(profile.get("username", "")).lower() != user.lower():
            return Result.error("Profile confirmation not found", url=show_url)

        return Result.taken(extra=_extract_profile(profile), url=show_url)

    return impersonate_validate(url, process, show_url=show_url)


def _extract_profile(profile: dict) -> dict:
    extra = {}

    for key, label in FIELDS.items():
        value = profile.get(key)
        if value in (None, "", [], {}) or str(value).lower() == "unknown":
            continue
        if _is_unset_number(value):
            continue
        extra[label] = re.sub(r"\s+", " ", str(value)).strip()

    if profile.get("height"):
        unit = "cm" if profile.get("heightUnit") == "metric" else "in"
        extra["height"] = f"{profile['height']} {unit}"

    # Body-type keys are gender-prefixed (femaleBodyType, maleType, ...).
    for key, value in profile.items():
        if re.fullmatch(r"(?:fe)?male(?:Body)?Type", key) and value:
            extra[re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()] = str(value)

    raw_languages = [profile.get("mainLanguage"), *(profile.get("secondaryLanguages") or [])]
    languages = [x for x in raw_languages if isinstance(x, str) and x]
    if languages:
        extra["languages"] = ", ".join(dict.fromkeys(languages))

    decorations = [x for x in (profile.get("bodyDecorations") or []) if isinstance(x, str)]
    if decorations:
        extra["body_decorations"] = ", ".join(decorations)

    for key, label in DATE_FIELDS.items():
        stamp = _date(profile.get(key))
        if stamp:
            extra[label] = stamp

    links = [v for v in (profile.get("socialNetworks") or {}).values() if isinstance(v, str) and v]
    if links:
        extra["social_links"] = ", ".join(links)

    wishlists = [v for v in (profile.get("wishList") or {}).values() if isinstance(v, str) and v]
    if wishlists:
        extra["wishlists"] = ", ".join(wishlists)

    return extra


def _is_unset_number(value) -> bool:
    # Unfilled numeric fields come back as 0 (e.g. age when no birth date is set).
    # Booleans are excluded because False is a real value and equals 0 in Python.
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0


def _date(value) -> str | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
