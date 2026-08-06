import base64
import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.npmjs.com"
NOT_FOUND_MESSAGE = "Scope not found"


def validate_npmjs(user: str) -> Result:
    """npm serves the scope page as JSON when asked with ``x-spiferack``, the
    header its own front end uses; ``/~<name>`` resolves both user and org
    scopes, so the account type comes from ``scope.type``.
    """
    if re.search(r"[A-Z]", user):
        return Result.error("Username cannot contain uppercase letters.")

    url = f"{BASE_URL}/~{user}"

    def process(response) -> Result:
        try:
            data = response.json()
        except Exception:
            return Result.error(f"Unexpected response status: {response.status_code}")

        if response.status_code == 404:
            if NOT_FOUND_MESSAGE in (data.get("message") or ""):
                return Result.available()
            return Result.error(f"Unexpected response body: {data.get('message')}")

        scope = data.get("scope") or {}
        parent = scope.get("parent") or {}
        if response.status_code == 200 and parent.get("name") == user:
            extra = _profile(data, scope, parent)
            media = {}
            if avatar := _avatar(parent):
                media["avatar"] = avatar
            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected response status: {response.status_code}")

    return impersonate_validate(
        url, process, headers={"x-spiferack": "1"}, show_url=url
    )


def _profile(data: dict, scope: dict, parent: dict) -> dict:
    resource = parent.get("resource") or {}
    extra: dict[str, str | int] = {}

    for value, key in (
        (scope.get("type"), "type"),
        (resource.get("fullname"), "fullname"),
        (parent.get("description"), "description"),
        (scope.get("id"), "id"),
        (scope.get("created"), "created"),
    ):
        if value:
            extra[key] = value

    if github := resource.get("github"):
        extra["github"] = f"https://github.com/{github}"

    packages = (data.get("packages") or {}).get("total")
    if packages is not None:
        extra["packages"] = packages

    return extra


def _avatar(parent: dict) -> str | None:
    """Avatars are served as ``/npm-avatar/<jwt>``; the unsigned payload holds
    the upstream image URL, which outlives the token wrapper.
    """
    path = (parent.get("avatars") or {}).get("large")
    if not path:
        return None

    try:
        payload = path.rsplit("/", 1)[-1].split(".")[1]
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        return json.loads(decoded)["avatarURL"]
    except Exception:
        return f"{BASE_URL}{path}"
