import html
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_pornhub(user):
    url = f"https://www.pornhub.com/users/{user}"

    def process(response):
        if (
            response.status_code == 404
            and "Error Page Not Found" in response.text
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        account_type = _account_type(str(response.url))
        extra = _extract_profile(response.text)
        confirmed = (
            account_type in ("viewer", "model", "pornstar") and "name" in extra
            or account_type == "channel"
            and "xxx videos" in _title(response.text).lower()
        )
        if confirmed:
            return Result.taken(extra={"type": account_type, **extra})

        return Result.error("Profile confirmation not found")

    return impersonate_validate(url, process, allow_redirects=True)


def _account_type(location: str) -> str | None:
    if match := re.search(r"/(pornstar|model|channels|users)/", location, re.IGNORECASE):
        namespace = match.group(1).lower()
        return {"channels": "channel", "users": "viewer"}.get(namespace, namespace)
    return None


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # Display name: viewer pages carry it in the "<name>'s Profile" title;
    # model/pornstar pages carry it in the <h1 itemprop="name"> heading.
    name = re.match(r"(.*?)'s Profile - Pornhub", _title(html_text), re.IGNORECASE)
    if name:
        extra["name"] = name.group(1).strip()
    else:
        heading = re.search(r'<h1 itemprop="name">\s*(.*?)\s*</h1>', html_text, re.IGNORECASE | re.DOTALL)
        if heading:
            extra["name"] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", heading.group(1)))).strip()

    # Stable numeric account id from the profile's own stream loader (viewers).
    user_id = re.search(r"stream_\w+\?load=public&(?:amp;)?user_id=(\d+)", html_text)
    if user_id:
        extra["user_id"] = user_id.group(1)

    # About Me / bio attributes, rendered identically on viewer, model, and
    # pornstar pages:
    #   <div class="infoPiece"><span>Label:</span><span class="smallInfo">Value</span></div>
    for piece in re.finditer(
        r'<div class="infoPiece">\s*<span>\s*(.*?)\s*</span>\s*'
        r'<span[^>]*class="smallInfo"[^>]*>\s*(.*?)\s*</span>',
        html_text, re.DOTALL):
        label = re.sub(r"\s+", " ", html.unescape(piece.group(1))).strip().rstrip(":")
        value = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(piece.group(2)))).strip()
        if label and value:
            extra[label] = value

    return extra


def _title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else ""
