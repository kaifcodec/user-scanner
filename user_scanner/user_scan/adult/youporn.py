import re
import html

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

BASE_URL = "https://www.youporn.com"

# Accounts are split across namespaces and a handle sits in only one, so every
# namespace must confirm the miss before a name counts as free. Note /user/ is
# NOT usable: it is a soft-200 catch-all that renders the generic home page for
# any string, echoing the handle only in canonical/hreflang boilerplate.
PROFILE_NAMESPACES = (("model", "pornstar"), ("amateur", "amateur"))


def validate_youporn(user: str) -> Result:
    show_url = f"{BASE_URL}/pornstar/{user}/"

    pending_error = None
    for account_type, path in PROFILE_NAMESPACES:
        url = f"{BASE_URL}/{path}/{user}/"
        try:
            # The geo redirect is a 302 to a country host, so redirects must be
            # followed.
            response = impersonate_request(url, allow_redirects=True)
        except Exception as e:
            pending_error = Result.error(e, url=show_url)
            continue

        # Only a real profile echoes the requested handle in its canonical link;
        # the host varies because YouPorn geo-redirects (e.g. br.youporn.com).
        if response.status_code == 200 and _canonical_profile(response.text, path) == user.lower():
            extra = {"type": account_type, **_extract_profile(response.text)}
            return Result.taken(extra=extra, url=url)

        # A genuinely missing handle 404s with the dedicated not-found template;
        # require its title so a blocked or transient 404 isn't read as free.
        if response.status_code == 404 and "404 page not found" in _title(response.text).lower():
            continue

        pending_error = Result.error(
            f"Unexpected response on /{path}/: {response.status_code}", url=show_url
        )

    viewer = _viewer_account(user)
    if viewer is not None:
        return viewer

    if pending_error:
        return pending_error
    return Result.available(url=show_url)


def _viewer_account(user: str) -> Result | None:
    """Plain accounts own no page under their handle; /uservids/<handle> is the
    only route that resolves them, and it canonicalises to /user/<numeric id>/.
    Returns None when the handle is confirmed missing so the caller falls
    through to `available`."""
    url = f"{BASE_URL}/uservids/{user}/"
    try:
        response = impersonate_request(url, allow_redirects=True)
    except Exception as e:
        return Result.error(e, url=url)

    if response.status_code == 200:
        user_id = re.search(r"/user/(\d+)", _canonical_href(response.text) or "")
        if user_id:
            return Result.taken(
                extra={"type": "viewer", "user_id": user_id.group(1)},
                url=f"{BASE_URL}/user/{user_id.group(1)}/",
            )
        return Result.error("Viewer confirmation not found", url=url)

    if response.status_code == 404 and "404 page not found" in _title(response.text).lower():
        return None

    # Some real accounts answer 500 here rather than rendering; that is neither a
    # confirmed hit nor a confirmed miss, so it is reported instead of guessed.
    return Result.error(f"Unexpected response on /uservids/: {response.status_code}", url=url)


def _canonical_href(html_text: str) -> str | None:
    link = re.search(r'<link\b[^>]*\brel="canonical"[^>]*>', html_text, re.IGNORECASE)
    if not link:
        return None

    href = re.search(r'href="([^"]+)"', link.group(0), re.IGNORECASE)
    return href.group(1) if href else None


def _canonical_profile(html_text: str, path: str) -> str | None:
    href = _canonical_href(html_text)
    if not href:
        return None

    match = re.search(rf"/{re.escape(path)}/([^/?#]+)", href, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _extract_profile(html_text: str) -> dict:
    extra = {}

    name = re.search(r'<h1 class="name-title">\s*(.*?)\s*</h1>', html_text, re.DOTALL)
    if name:
        extra["name"] = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", name.group(1)))).strip()

    # The stats bar and the bio table share this label/value markup, so one pass
    # captures rank/views/subscribers plus every bio field the model filled in.
    # Labels follow the geo-served locale (YouPorn redirects by IP and honours
    # no lang override), so a few keys arrive translated — values do not.
    for stat in re.finditer(
        r'<p class="info-stat-label">\s*(.*?)\s*</p>\s*<p class="info-stat-data">\s*(.*?)\s*</p>',
        html_text, re.DOTALL):
        label = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", stat.group(1)))).strip().lower()
        value = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", stat.group(2)))).strip()
        if label and value:
            extra[label.replace(" ", "_")] = value

    # Images lazy-load, so the real URL sits in data-src; src is a placeholder
    # GIF. The banner shares the markup, hence the avatar-wrapper anchor.
    avatar = re.search(
        r'<div class="avatar-wrapper">.*?\bdata-src="([^"]+)"', html_text, re.DOTALL | re.IGNORECASE)
    if avatar:
        extra["avatar"] = html.unescape(avatar.group(1))

    return extra


def _title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else ""
