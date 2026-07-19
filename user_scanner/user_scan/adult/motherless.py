import re
from user_scanner.core.orchestrator import generic_validate, make_request, Result

CHECK_URL = "https://motherless.xxx/register/checkusername"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://motherless.xxx",
    "Referer": "https://motherless.xxx/register",
}


def validate_motherless(user):
    show_url = f"https://motherless.xxx/m/{user}"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        body = response.text

        # The field check reuses "not-available" for both taken names and
        # rejected input (e.g. "Username is invalid.").
        if 'class="not-available"' in body:
            if "invalid" in body.lower():
                return Result.error("Username rejected by Motherless", url=show_url)
            return Result.taken(extra=_fetch_profile(show_url), url=show_url)

        if 'class="available"' in body:
            return Result.available(url=show_url)

        return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

    return generic_validate(
        CHECK_URL, process, show_url=show_url, method="POST", data={"username": user}, headers=HEADERS
    )


def _fetch_profile(profile_url: str) -> dict:
    """The checkusername endpoint only reports availability, so pull the public
    member page for metadata. Best-effort: a failed fetch yields no extra."""
    try:
        response = make_request(profile_url)
        if response.status_code != 200:
            return {}
        return _extract_profile(response.text)
    except Exception:
        return {}


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # The public member page renders two field blocks: "profile-stats" rows
    # (<span>Label:</span> value) and "profile-member-info" rows
    # (<strong>Label</strong> <span>value</span>). Pull every row rather than a
    # fixed subset so whatever the member fills in is captured. Zero counts are
    # dropped as noise.
    for row in re.finditer(r'<div class="profile-stats">\s*<span>([^<]+?):\s*</span>\s*(.*?)\s*</div>', html_text, re.DOTALL):
        label = re.sub(r"\s+", " ", row.group(1)).strip()
        value = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row.group(2))).strip()
        if value and value != "0":
            extra[label] = value

    for row in re.finditer(r'<div class="profile-member-info[^"]*">\s*<strong>([^<]+?)</strong>\s*<span>\s*(.*?)\s*</span>', html_text, re.DOTALL):
        label = re.sub(r"\s+", " ", row.group(1)).strip()
        value = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row.group(2))).strip()
        if value:
            extra[label] = value

    avatar = re.search(r'og:image"\s+content="([^"]+)"', html_text, re.IGNORECASE)
    if avatar:
        extra["avatar"] = avatar.group(1)

    return extra
