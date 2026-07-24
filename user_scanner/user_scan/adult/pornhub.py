import re
import html

from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.pornhub.com"


def validate_pornhub(user):
    url = f"{BASE_URL}/users/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        # A vanity handle that resolves to a real profile — a renamed handle
        # (/users/<id>) or a promoted model/pornstar page — 301-redirects; a
        # genuinely missing user just 404s. The target namespace tells us the
        # account type, and we follow it to enrich the metadata.
        if response.status_code in (301, 302):
            location = response.headers.get("location", "")
            account_type = _account_type(location)
            if account_type:
                return Result.taken(extra={"type": account_type, **_follow(location)}, url=show_url)
            return Result.error(f"Unexpected redirect: {location}", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A direct 200 on /users/<name> is always a viewer account (models and
        # pornstars redirect); the not-found page is titled "Page Not Found".
        if "profile - pornhub" in _title(response.text).lower():
            return Result.taken(extra={"type": "viewer", **_extract_profile(response.text)}, url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return impersonate_validate(url, process, show_url=show_url)


def _account_type(location: str) -> str | None:
    # Map the redirect target's namespace to an account type; None means the
    # redirect is not a recognised profile path.
    for namespace, label in (("pornstar", "pornstar"), ("model", "model"),
                             ("channels", "channel"), ("users", "viewer")):
        if re.search(rf"/{namespace}/", location, re.IGNORECASE):
            return label
    return None


def _follow(location: str) -> dict:
    # Model/pornstar pages hold far richer metadata than the viewer profile that
    # redirected here; the enrichment is best-effort and never fatal.
    url = location if location.startswith("http") else BASE_URL + location
    try:
        response = impersonate_request(url, allow_redirects=True)
        if response.status_code != 200:
            return {}
        return _extract_profile(response.text)
    except Exception:
        return {}


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
