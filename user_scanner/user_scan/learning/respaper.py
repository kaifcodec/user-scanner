import html
import re
from urllib.parse import quote, urljoin

import httpx

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result

BASE_URL = "https://www.respaper.com"


def validate_respaper(user: str) -> Result:
    encoded_user = quote(user, safe="")
    url = f"{BASE_URL}/{encoded_user}/about"

    def process(response) -> Result:
        if response.status_code == 404:
            if "The requested page was not found." in response.text:
                return Result.available()
            return Result.error("Unexpected 404 response")

        canonical = re.search(
            r'<link rel="canonical" href="([^"]+)"', response.text
        )
        if response.status_code == 200 and canonical:
            if canonical.group(1).lower() != f"/{encoded_user}/about".lower():
                return Result.error("Profile resolved to a different username")

            extra = _extract_profile(response.text)
            media = {}

            avatar = re.search(
                r'<td[^>]+class="user_info_container"[^>]*>\s*<img[^>]+src="([^"]+)"',
                response.text,
            )
            if avatar and not avatar.group(1).endswith("/p.jpg"):
                avatar_url = urljoin(url, avatar.group(1))
                try:
                    avatar_response = make_request(
                        avatar_url, method="HEAD", follow_redirects=True
                    )
                except httpx.HTTPError:
                    pass
                else:
                    # ResPaper serves its shared default GIF from some user-specific
                    # .jpg URLs; uploaded profile photos are normalized to JPEG.
                    if (
                        avatar_response.status_code == 200
                        and avatar_response.headers.get("content-type") == "image/jpeg"
                    ):
                        media["avatar"] = avatar_url

            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=url, follow_redirects=True)


def _extract_profile(page: str) -> dict[str, object]:
    extra: dict[str, object] = {}
    name = re.search(
        r'<h1[^>]*class="[^"]*\bDispDesc\b[^"]*"[^>]*>'
        r"(.*?) &minus; Profile</h1>",
        page,
        re.DOTALL,
    )
    if name:
        extra["fullname"] = _text(name.group(1))

    for source, target, separator in (
        ("City", "city", None),
        ("State", "state", None),
        ("Country", "country", None),
        ("Organization", "organization", None),
        ("NextDestination", "next_destination", None),
        ("LifeGoals", "life_goals", None),
        ("HobbiesSports", "hobbies_sports", r"(?:<br\s*/?>|\r?\n)+"),
        ("Languages", "languages", r"[,;\r\n]+"),
    ):
        value = re.search(
            rf'id="my_{source}"[^>]*>(.*?)</(?:span|pre)>', page, re.DOTALL
        )
        if not value:
            continue
        if separator and (items := _values(value.group(1), separator)):
            extra[target] = items
        elif not separator and (cleaned := _text(value.group(1))):
            extra[target] = cleaned.rstrip(",") if target == "city" else cleaned

    sections = _sections(page)
    interests = [text for text, _ in _links(_section(sections, "Interested in")) if text]
    if interests:
        extra["exam_interests"] = interests

    if education := _education(page):
        extra["education"] = education

    for heading, key in (("Class Pages", "class_pages"), ("Groups", "groups")):
        if memberships := _memberships(_section(sections, heading)):
            extra[key] = memberships

    for heading, key in (
        ("Faves", "faves_count"),
        ("In Faves Of", "in_faves_of_count"),
    ):
        if count := re.search(rf"{heading} \((\d+)\)", page):
            extra[key] = int(count.group(1))

    recently_viewed = _links(
        _section(sections, "Recently Viewed ResPapers"), items_only=True
    )
    extra["recently_viewed_count"] = sum(
        bool(text and text != "More...") for text, _ in recently_viewed
    )

    uploads = [
        f"{text} ({urljoin(BASE_URL, href)})"
        for text, href in _links(
            _section(sections, "ResPapers Uploaded by"), items_only=True
        )
        if text and text != "More..."
    ]
    if uploads:
        extra["uploads"] = uploads

    extra["recent_responses_count"] = len(
        re.findall(
            r'<table\b[^>]*id="resp_[^"]+"',
            _section(sections, "Recent Responses by"),
        )
    )

    if scores := _scores(_section(sections, "Scores")):
        extra["scores"] = scores

    return extra


def _sections(page: str) -> list[tuple[str, str]]:
    headings = list(
        re.finditer(r'<p class="tdheader_sch">(.*?)</p>', page, re.DOTALL)
    )
    return [
        (_text(match.group(1)).rstrip(" :"), page[match.end() : next_start])
        for match, next_start in zip(
            headings, [item.start() for item in headings[1:]] + [len(page)]
        )
    ]


def _section(sections: list[tuple[str, str]], prefix: str) -> str:
    return next((body for heading, body in sections if heading.startswith(prefix)), "")


def _links(markup: str, *, items_only: bool = False) -> list[tuple[str, str]]:
    item_filter = r'(?=[^>]*class="[^"]*\bmFont\b)' if items_only else ""
    return [
        (_text(label), html.unescape(href))
        for href, label in re.findall(
            rf'<a\b{item_filter}[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            markup,
            re.DOTALL,
        )
    ]


def _education(page: str) -> list[dict[str, str | int]]:
    education = []
    for entry in re.findall(
        r'<table[^>]+class="education_elem"[^>]*>(.*?)</table>', page, re.DOTALL
    ):
        item: dict[str, str | int] = {}
        fields = {
            "school": re.search(r'id="ed_name_\d+"[^>]*>(.*?)</span>', entry, re.DOTALL),
            "address": re.search(r'id="ed_desc_\d+"[^>]*>(.*?)</span>', entry, re.DOTALL),
            "comment": re.search(
                r'id="rating_comment_span_\d+"[^>]*>(.*?)</span>', entry, re.DOTALL
            ),
        }
        item.update(
            (key, value)
            for key, match in fields.items()
            if match and (value := _text(match.group(1)).strip('"'))
        )
        if count := re.search(r">\+(\d+)</a>", entry):
            item["school_member_count"] = int(count.group(1))
        if rating := re.search(r'class="rateit"[^>]+data-score="(\d+)"', entry):
            item["rating"] = int(rating.group(1))
        if item:
            education.append(item)
    return education


def _memberships(markup: str) -> list[dict[str, str]]:
    memberships = []
    for entry in re.findall(
        r'<table[^>]+id="mygrp_\d+"[^>]*>(.*?)</table>', markup, re.DOTALL
    ):
        group = re.search(
            r'<b>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', entry, re.DOTALL
        )
        if not group:
            continue
        item = {
            "name": _text(group.group(2)),
            "url": urljoin(BASE_URL, html.unescape(group.group(1))),
        }
        school = re.search(r'<a[^>]+href="/s/[^"]+"[^>]*>(.*?)</a>', entry, re.DOTALL)
        if school:
            item["school"] = _text(school.group(1))
        memberships.append(item)
    return memberships


def _scores(markup: str) -> list[dict[str, str | int]]:
    scores = []
    for exam, table in re.findall(
        r'<a[^>]+href="[^"]+-scp\.html"[^>]*>(.*?)</a>.*?'
        r'<table[^>]+id="rtable"[^>]*>(.*?)</table>',
        markup,
        re.DOTALL,
    ):
        for row in re.findall(r'<tr class="row\d+">(.*?)</tr>', table, re.DOTALL):
            mark = re.search(r"<b>([^<]+)</b>", row)
            likes = re.search(r'id="milikes_span\d+">([^<]+)', row)
            school = re.search(r'href="/s/[^"?]+[^>]*>(.*?)</a>', row, re.DOTALL)
            remark = re.search(r'class="detailstd">(.*?)</td>', row, re.DOTALL)
            score: dict[str, str | int] = {
                "exam": _text(exam).removesuffix(" - Share Your Result!")
            }
            if mark:
                score["marks"] = _text(mark.group(1))
            if likes:
                score["likes"] = int(_text(likes.group(1)))
            if school:
                score["school"] = _text(school.group(1))
            if remark:
                score["remarks"] = _text(remark.group(1))
            scores.append(score)
    return scores


def _text(markup: str) -> str:
    return re.sub(
        r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))
    ).strip()


def _values(markup: str, separator: str) -> list[str]:
    return [value for item in re.split(separator, markup) if (value := _text(item))]
