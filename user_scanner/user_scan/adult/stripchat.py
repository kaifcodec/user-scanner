import re
import json

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://stripchat.com"
API_URL = f"{BASE_URL}/api/front"

# Profile fields worth surfacing, mapped to friendlier extra keys.
FIELDS = {
    "id": "user_id",
    "name": "name",
    "previousUsername": "previous_username",
    "age": "age",
    "birthDate": "birth_date",
    "gender": "gender",
    "genderDoc": "gender_doc",
    "country": "country",
    "region": "region",
    "city": "city",
    "ethnicity": "ethnicity",
    "hairColor": "hair_color",
    "eyeColor": "eye_color",
    "bodyType": "body_type",
    "interestedIn": "interested_in",
    "subculture": "subculture",
    "description": "bio",
    "offlineStatus": "status_message",
    "favoritedCount": "favorites",
    "isOnline": "is_online",
    "isLive": "is_live",
    "isPornStar": "is_pornstar",
    "createdAt": "created_at",
    "avatarUrl": "avatar",
}


def validate_stripchat(user: str) -> Result:
    url = f"{BASE_URL}/{user}"
    show_url = url

    def process(response):
        # The 404 page still echoes the requested handle, so the verdict rests on
        # the embedded error object, not on the handle appearing in the body.
        if response.status_code == 404:
            if '"type":"notFound"' in response.text:
                return Result.available(url=show_url)
            return Result.error("Unexpected 404 (not the not-found payload)", url=show_url)

        # Viewer (non-broadcasting) accounts live under /user/, and the site only
        # redirects there when the account exists — an unknown handle 404s
        # instead. The page itself is client-rendered, so the profile is pulled
        # from the same front API the page calls.
        if response.status_code in (301, 302):
            location = response.headers.get("location", "")
            if re.fullmatch(rf"(?:https?://[^/]+)?/user/{re.escape(user)}/?", location, re.IGNORECASE):
                extra = {"type": "viewer", **_api_profile(user)}
                return Result.taken(extra=extra, url=f"{BASE_URL}/user/{user}")
            return Result.error(f"Unexpected redirect: {location}", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        model = _model_object(response.text, user)
        if model:
            return Result.taken(extra={"type": "model", **_extract_profile(model)}, url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return impersonate_validate(url, process, show_url=show_url)


def _api_profile(user: str) -> dict:
    """Viewer pages render client-side, so read the same front API the page calls:
    the handle resolves to a numeric id, then the account and profile documents.
    Both use the same field names as the embedded model object, so they feed the
    shared extractor. Best-effort — a failure just yields no extra."""
    try:
        response = impersonate_request(f"{API_URL}/users/user-ids/{user}", allow_redirects=True)
        if response.status_code != 200:
            return {}
        user_id = json.loads(response.text).get("id")
        if not user_id:
            return {}

        merged: dict = {}
        for path in (f"/v2/users/{user_id}", f"/v2/users/{user_id}/profile"):
            document = impersonate_request(f"{API_URL}{path}", allow_redirects=True)
            if document.status_code == 200:
                merged.update(json.loads(document.text).get("item") or {})
        return _extract_profile(merged) if merged else {}
    except Exception:
        return {}


def _model_object(html_text: str, user: str) -> dict:
    """Pull the preloaded-state `model` object whose username matches the
    request. The page embeds several `"model":{...}` nodes (player, knights),
    so each candidate is parsed and matched rather than taking the first."""
    for match in re.finditer(r'"model":\{', html_text):
        raw = _json_object_at(html_text, match.end() - 1)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if str(data.get("username", "")).lower() == user.lower():
            return data
    return {}


def _json_object_at(text: str, start: int) -> str | None:
    # Brace-match from an opening '{', ignoring braces inside string literals,
    # to slice out a complete JSON object embedded in the page.
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _extract_profile(model: dict) -> dict:
    extra = {}

    for key, label in FIELDS.items():
        value = model.get(key)
        if value in (None, "", [], {}) or _is_unset_number(value):
            continue
        extra[label] = _clean(key, value)

    languages = [x for x in (model.get("languages") or []) if isinstance(x, str)]
    if languages:
        extra["languages"] = ", ".join(languages)

    # Body/appearance tags arrive prefixed ("specificBubblebutt", "hairLengthLong").
    specifics = [_strip_prefix(x) for x in (model.get("specifics") or []) if isinstance(x, str)]
    if specifics:
        extra["specifics"] = ", ".join(specifics)

    interests = [x for x in (model.get("interests") or []) if isinstance(x, str)]
    if interests:
        extra["interests"] = ", ".join(interests)

    return extra


def _is_unset_number(value) -> bool:
    # Unfilled numeric fields come back as 0 (age, favourites). Booleans are
    # excluded because False is a real value here and equals 0 in Python.
    return isinstance(value, int) and not isinstance(value, bool) and value == 0


def _clean(key: str, value) -> str:
    # Enum-style values repeat their own field name ("ethnicityWhite",
    # "bodyTypeAverage"); drop that prefix so the output reads plainly.
    if isinstance(value, str) and value.lower().startswith(key.lower()):
        return _strip_prefix(value, key)
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return str(value)


def _strip_prefix(value: str, key: str = "") -> str:
    if key and value.lower().startswith(key.lower()):
        value = value[len(key):]
    else:
        value = re.sub(r"^(?:specifics?|hairLength)", "", value)
    return value[:1].upper() + value[1:] if value else value
