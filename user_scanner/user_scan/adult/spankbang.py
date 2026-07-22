import re
import html

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_spankbang(user):
    url = f"https://spankbang.com/profile/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile answers 200 with a "<user> Profile ... @ SpankBang"
        # title; the not-found page is a 200-less generic front page.
        if _is_profile(response.text, user):
            return Result.taken(extra=_extract_profile(response.text), url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return impersonate_validate(url, process, show_url=show_url)


def _is_profile(html_text: str, user: str) -> bool:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return False

    title = match.group(1).strip().lower()
    return title.startswith(user.lower() + " profile") and "spankbang" in title


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # The OpenGraph tags are templated boilerplate here, so read the real
    # server-rendered profile markup instead.
    name = re.search(r'<h1 class="profile_name">\s*([^<]+?)\s*</h1>', html_text, re.IGNORECASE)
    if name:
        extra["name"] = html.unescape(name.group(1)).strip()

    # Stable numeric account id (the handle can be changed; this cannot).
    user_id = re.search(r"ana_profile_id\s*=\s*'(\d+)'", html_text)
    if user_id:
        extra["user_id"] = user_id.group(1)

    # Country comes from the flag image filename (ISO code), which is stable
    # regardless of the page language.
    country = re.search(r'class="flag"[^>]*/Flags/([A-Za-z]{2})\.png', html_text, re.IGNORECASE | re.DOTALL)
    if country:
        extra["country"] = country.group(1).upper()

    # Gender and age render in the details block; age is only present when set.
    gender = re.search(r'<span class="gender">\s*([^<]+?)\s*</span>', html_text, re.IGNORECASE)
    if gender:
        extra["gender"] = gender.group(1).strip()

    age = re.search(r'<span class="age">\s*(\d+)\s*</span>', html_text, re.IGNORECASE)
    if age:
        extra["age"] = age.group(1)

    # Avatar is a Gravatar keyed on the MD5 of the account email — useful for
    # cross-referencing even when it falls back to the robohash default.
    avatar = re.search(r'class="avatar"[^>]*?src="([^"]+)"', html_text, re.IGNORECASE)
    if avatar:
        extra["avatar"] = html.unescape(avatar.group(1).strip())

    # Stat tabs render as <a href="/profile/<user>/<slug>">Label <span>N</span></a>.
    # Key off the URL slug rather than the visible label so localisation never
    # breaks extraction; the visible label between > and <span> is ignored.
    for match in re.finditer(
        r'/profile/[^/"]+/([a-z_]+)"[^>]*>[^<]*<span>\s*([\d,.]+[KMk]?)\s*</span>',
        html_text, re.IGNORECASE):
        slug = match.group(1).lower()
        count = match.group(2)
        if slug not in extra and count not in ("0", ""):
            extra[slug] = count

    return extra
