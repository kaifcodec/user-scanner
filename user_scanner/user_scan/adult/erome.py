import re
import html

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.erome.com"


def validate_erome(user: str) -> Result:
    url = f"{BASE_URL}/{user}"
    show_url = url

    def process(response):
        # A handle whose account was removed answers 410 with a "User deleted"
        # page. The name is neither free nor backed by a profile, so it is
        # reported rather than turned into a verdict.
        if response.status_code == 410:
            if "user deleted" in _headings(response.text):
                return Result.error("Account deleted by EroMe", url=show_url)
            return Result.error("Unexpected 410 (not the deleted-user page)", url=show_url)

        if response.status_code == 404:
            if "page not found" in _headings(response.text):
                return Result.available(url=show_url)
            return Result.error("Unexpected 404 (not the not-found page)", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile is titled "<handle> - Profile page - EroMe"; the miss
        # pages fall back to the generic site title.
        name = re.match(r"(.*?) - Profile page - EroMe$", _title(response.text), re.IGNORECASE)
        if name and name.group(1).lower() == user.lower():
            return Result.taken(extra=_extract_profile(response.text), url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)


def _extract_profile(html_text: str) -> dict:
    extra = {}

    name = re.search(r"<h1[^>]*>\s*(.*?)\s*</h1>", html_text, re.DOTALL)
    if name:
        extra["name"] = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", name.group(1)))).strip()

    # The report control carries the account's numeric id — the only stable
    # identifier on the page, since the handle itself can change.
    user_id = re.search(r'data-var1="(\d+)"', html_text)
    if user_id:
        extra["user_id"] = user_id.group(1)

    # The stats row renders each figure as "<icon/>N <span>LABEL</span>"
    # (ALBUMS, VIEWS, FOLLOWERS, FOLLOWING).
    for stat in re.finditer(r"</svg>\s*([\d.,]+[KMkm]?)\s*<span[^>]*>\s*([A-Za-z]+)\s*</span>", html_text):
        value, label = stat.group(1), stat.group(2).lower()
        if value != "0":
            extra[label] = value

    # Account age is only exposed as a badge tooltip (e.g. "> 1 year(s)").
    seniority = re.search(
        r'<div class="badge"[^>]*title="([^"]*year\(s\)[^"]*)"', html_text, re.IGNORECASE)
    if seniority:
        extra["seniority"] = html.unescape(seniority.group(1)).strip()

    return extra


def _headings(html_text: str) -> str:
    return " ".join(
        re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", block)).strip().lower()
        for block in re.findall(r"<h1[^>]*>.*?</h1>|<h2[^>]*>.*?</h2>", html_text, re.DOTALL)
    )


def _title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else ""
