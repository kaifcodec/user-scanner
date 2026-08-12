import html
import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

# Academia.edu scopes handles per subdomain: the same slug can belong to a
# different person on an institution host (e.g. ucp.academia.edu). Only the
# independent-researcher namespace is checkable without enumerating every
# institution subdomain, so a verdict here covers that namespace alone.
BASE_URL = "https://independent.academia.edu"


def validate_academia(user: str) -> Result:
    url = f"{BASE_URL}/{user}"

    # Rails reads the segment after a dot as a format extension, so
    # "/John.Smith" serves the unrelated profile "/john". Such a handle is not
    # addressable and must not be turned into a verdict.
    if "." in user:
        return Result.error("Handles containing a period are not addressable", url=url)

    def process(response):
        if response.status_code == 404:
            if "wrong aisle" in response.text:
                return Result.available(url=url)
            return Result.error("Unexpected 404 (not the not-found page)", url=url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=url)

        profile = _profile_json(response.text)
        if profile is None:
            return Result.error("Profile confirmation not found", url=url)

        # A miss redirects rather than 404s in some casings, and the dot route
        # above lands on a foreign profile, so the embedded canonical handle is
        # what confirms the page belongs to the requested user.
        handle = str(profile.get("mainEntity", {}).get("url", "")).rstrip("/").rsplit("/", 1)[-1]
        if handle.lower() != user.lower():
            return Result.error(f"Profile resolved to a different handle: {handle}", url=url)

        extra, media = _extract_profile(response.text, profile)
        return Result.taken(extra=extra, media=media, url=url)

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)


def _profile_json(html_text: str) -> dict | None:
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html_text, re.DOTALL
    ):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "ProfilePage":
            return data
    return None


def _extract_profile(html_text: str, profile: dict) -> tuple[dict, dict]:
    person = profile.get("mainEntity", {})
    extra: dict = {"name": person.get("name")}
    media: dict = {}

    avatar = person.get("image")
    if avatar and "no_pic" not in avatar:
        media["avatar"] = avatar

    for key, field in (("joined", "dateCreated"), ("updated", "dateModified")):
        value = profile.get(field)
        if value:
            extra[key] = value[:10]

    extra["bio"] = profile.get("description")

    links = person.get("sameAs") or profile.get("sameAs")
    if links:
        extra["links"] = ", ".join(links)

    affiliation = re.search(
        r'class="affiliations-container[^"]*"[^>]*>(.*?)</div>', html_text, re.DOTALL
    )
    if affiliation:
        extra["affiliation"] = _text(affiliation.group(1))

    # Every follow control on the page belongs to the profile owner; the
    # related-author cards carry no user id of their own.
    user_id = re.search(r'data-follow-user-id="(\d+)"', html_text)
    if user_id:
        extra["user_id"] = user_id.group(1)
        extra.update(_extract_interests(html_text, user_id.group(1)))

    extra.update(_extract_stats(html_text))
    extra.update(_extract_bio_details(html_text))

    return extra, media


def _extract_interests(html_text: str, user_id: str) -> dict:
    interests = {}

    total = re.search(
        rf'data-has-card-for-ri-list="{user_id}"[^>]*>View All \((\d+)\)', html_text
    )
    if total:
        interests["interests_count"] = total.group(1)

    # The interest pills render as sibling React payloads; keying the enclosing
    # anchor on the owner's id keeps a recommendation carousel out of the list.
    labels: list[str] = []
    for anchor in re.findall(
        rf'data-has-card-for-ri-list="{user_id}"(.*?)</a>', html_text, re.DOTALL
    ):
        pill = re.search(r'data-component-name="Pill"[^>]*>(\{.*?\})</script>', anchor, re.DOTALL)
        if not pill:
            continue
        try:
            children = json.loads(pill.group(1)).get("children") or []
        except ValueError:
            continue
        labels.extend(str(child) for child in children)

    if labels:
        interests["interests"] = ", ".join(labels)

    return interests


def _extract_stats(html_text: str) -> dict:
    region = re.search(r'class="user-stats-container"(.*?)<aside', html_text, re.DOTALL)
    if not region:
        return {}

    stats = {}
    for label, value in re.findall(
        r'<p class="label">(.*?)</p>\s*<p class="data">(.*?)</p>', region.group(1), re.DOTALL
    ):
        stats[_text(label)] = _text(value)
    return stats


def _extract_bio_details(html_text: str) -> dict:
    bio = re.search(r'class="profile-bio[^"]*"[^>]*>(.*?)</div>', html_text, re.DOTALL)
    if not bio:
        return {}

    return {
        _text(label): _text(value)
        for label, value in re.findall(
            r'<span class="u-fw700">(.*?):.*?</span>(.*?)<br\s*/?>', bio.group(1), re.DOTALL
        )
    }


def _text(html_fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", html_fragment))).strip()
