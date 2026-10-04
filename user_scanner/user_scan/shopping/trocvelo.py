import re
import unicodedata
from urllib.parse import urljoin

from curl_cffi.requests.exceptions import RequestException

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

API_URL = "https://api.troc-velo.com/api/users"
SITE_URL = "https://www.troc-velo.com/fr-fr"
INTERESTS = {
    "1": "Vélo de route",
    "2": "VTT",
    "3": "Triathlon",
    "4": "Gravel",
    "5": "Urbain",
}


def validate_trocvelo(user: str) -> Result:
    username = user.strip()
    try:
        response = impersonate_request(
            f"{API_URL}/check_username",
            method="POST",
            json={"username": username},
            headers={"Accept": "application/json"},
        )
        if response.status_code != 200:
            return Result.error(
                f"Unexpected response status: {response.status_code}", url=SITE_URL
            )

        if (data := _json_object(response)) is None:
            return Result.error("Unexpected response body", url=SITE_URL)

        exists = data.get("exists")
        if exists is False:
            return Result.available(url=SITE_URL)
        if exists is not True:
            return Result.error("Username status was missing", url=SITE_URL)

        extra, media, profile_url = _profile(username)
        return Result.taken(extra=extra, media=media, url=profile_url or SITE_URL)
    except RequestException as exc:
        return Result.error(exc, url=SITE_URL)


def _json_object(response) -> dict | None:
    try:
        data = response.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _profile(username: str) -> tuple[dict, dict, str | None]:
    url = API_URL
    params: dict[str, object] | None = {
        "usernameCanonical": username,
        "itemsPerPage": 1000,
    }
    while True:
        response = impersonate_request(
            url, params=params, headers={"Accept": "application/ld+json"}
        )
        if response.status_code != 200:
            return {}, {}, None

        if (data := _json_object(response)) is None:
            return {}, {}, None

        members = data.get("hydra:member", [])
        if not isinstance(members, list):
            return {}, {}, None

        member = next(
            (
                item
                for item in members
                if isinstance(item, dict)
                and str(item.get("username", "")).casefold() == username.casefold()
            ),
            None,
        )
        if member:
            break

        view = data.get("hydra:view")
        next_page = view.get("hydra:next") if isinstance(view, dict) else None
        if not isinstance(next_page, str):
            return {}, {}, None
        url, params = urljoin(API_URL, next_page), None

    if not (slug := member.get("slug")):
        return {}, {}, None

    route = _slugify(str(member.get("username", "")))
    profile_url = f"{SITE_URL}/user/{route}/{slug}" if route else None
    response = impersonate_request(
        f"{API_URL}/{slug}", headers={"Accept": "application/ld+json"}
    )
    if response.status_code != 200:
        return {}, {}, profile_url

    if (profile := _json_object(response)) is None:
        return {}, {}, profile_url

    extra = {
        (
            f"{_snake_case(key)}_reviews" if key.endswith("Star") else _snake_case(key)
        ): value
        for key, value in profile.items()
        if not key.startswith("@")
        and key
        not in {
            "avatar",
            "country",
            "countryOfResidence",
            "interests",
            "nationality",
            "username",
            "userBanner",
            "userProConfiguration",
        }
    }
    for key in ("country", "nationality", "countryOfResidence"):
        value = profile.get(key)
        extra[_snake_case(key)] = (
            value.get("name") if isinstance(value, dict) else value
        )

    configuration = profile.get("userProConfiguration")
    if isinstance(configuration, dict):
        extra.update(
            {
                _snake_case(key): value
                for key, value in configuration.items()
                if not key.startswith("@")
            }
        )

    interests = profile.get("interests") or []
    extra["interests"] = [INTERESTS.get(str(value), str(value)) for value in interests]
    extra = {key: value for key, value in extra.items() if value != []}
    media = {"avatar": profile.get("avatar"), "banner": profile.get("userBanner")}
    return extra, media, profile_url


def _slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _snake_case(value: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value).lower()
