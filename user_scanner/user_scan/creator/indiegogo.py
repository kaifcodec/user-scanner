import json
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_indiegogo(user: str) -> Result:
    url = f"https://www.indiegogo.com/en/profile/{quote(user, safe='')}"

    def process(response):
        body = response.text
        if response.status_code == 404 and "<title>404: Page Not Found - Indiegogo</title>" in body:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        props = _props(body)
        if not props or str(props.get("userUrlName", "")).casefold() != user.casefold():
            return Result.error("200 without the matching Indiegogo account data")

        extra = {"id": props.get("userID"), "name": props.get("nickname")}
        for key, value in (props.get("navigationCounters") or {}).items():
            extra[key.removesuffix("Count")] = value

        return Result.taken(extra=extra, media={"avatar": props.get("avatarUrl")})

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)


def _props(body: str) -> dict | None:
    marker = "'App.Views.UserProfileView', App.Views.UserProfileView, "
    start = body.find(marker)
    if start == -1:
        return None

    start = body.find('{"props":', start)
    end = body.find(");</script>", start)
    if start == -1 or end == -1:
        return None

    props = json.loads(body[start:end]).get("props")
    return props if isinstance(props, dict) else None
