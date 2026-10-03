import html
import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


HUMAN_COOKIE = "LTUnifiedCookie=%7B%22areyouhuman%22%3A1%7D"
MEMBER_RE = re.compile(
    r'<h1>Member&thinsp;<i[^>]*>.*?</i>([^<]+)'
    r'(?:<span class="user_pronoun">\(([^<]+)\)</span>)?</h1>',
    re.IGNORECASE | re.DOTALL,
)

SCALAR_FIELDS = {
    "Real Name": "real_name",
    "Joined": "joined",
    "About Me": "bio",
    "Location": "location",
    "Homepage": "homepage",
    "About My Library": "about_library",
}

LIST_FIELDS = {
    "Also On": "also_on",
    "Memberships": "memberships",
    "Currently Reading": "currently_reading",
    "Favorite Authors": "favorite_authors",
    "Favorite Lists": "favorite_lists",
    "Groups": "groups",
    "Friends": "friends",
    "Interesting Library": "interesting_library",
    "Contacts": "contacts",
    "Local Favorites": "local_favorites",
}


def validate_librarything(user: str) -> Result:
    url = f"https://www.librarything.com/profile/{urllib.parse.quote(user, safe='')}"

    def process(response) -> Result:
        body = response.text
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")
        if "Error: This user doesn't exist" in body:
            return Result.available()

        member = MEMBER_RE.search(body)
        if (
            not member
            or html.unescape(member.group(1)).strip().casefold() != user.casefold()
        ):
            return Result.error("200 response with no matching member profile")

        fields = dict(
            re.findall(
                r"<dt>([^<]+)</dt><dd>(.*?)</dd>", body, re.IGNORECASE | re.DOTALL
            )
        )
        extra: dict[str, str | int | list[str]] = {
            key: _clean(fields.get(label, ""))
            for label, key in SCALAR_FIELDS.items()
        }
        for label, key in LIST_FIELDS.items():
            if items := _items(fields.get(label, "")):
                extra[key] = items
        if member.group(2):
            extra["pronouns"] = member.group(2)
        for label in ("Books", "Collections", "Reviews", "Recommendations", "Pictures"):
            count = re.search(rf"([\d,]+) {label}", body, re.IGNORECASE)
            if count:
                extra[label.lower()] = int(count.group(1).replace(",", ""))
        links = re.findall(r'href="(https?://[^"]+)"', fields.get("Also On", ""))
        if links:
            extra["external_profiles"] = list(map(html.unescape, links))
        if profile_id := re.search(
            r'class="ff_useraction"><a data-profileid="(\d+)"', body
        ):
            extra["profile_id"] = int(profile_id.group(1))

        return Result.taken(
            extra=extra,
            media={"avatar": _avatar(body)},
        )

    return impersonate_validate(
        url,
        process,
        headers={"Cookie": HUMAN_COOKIE},
    )


def _clean(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def _items(value: str) -> list[str]:
    items = re.findall(
        r'class="ltil_item[^"]*"[^>]*>(.*?)</(?:span|div)>',
        value,
        re.IGNORECASE | re.DOTALL,
    )
    return [value for item in items if (value := _clean(item).rstrip(",; "))]


def _avatar(body: str) -> str:
    image = re.search(
        r'class="pagecard_content_img".*?<img([^>]+)>',
        body,
        re.IGNORECASE | re.DOTALL,
    )
    if not image:
        return ""
    srcset = re.search(r'srcset="([^"]+)"', image.group(1))
    if srcset:
        sources = re.findall(r"(https?://\S+)\s+\d+x", html.unescape(srcset.group(1)))
        if sources:
            return sources[-1]
    src = re.search(r'src="([^"]+)"', image.group(1))
    return html.unescape(src.group(1)) if src else ""
