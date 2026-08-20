import json
import re
from datetime import datetime, timezone
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def _meta(document: str, name: str) -> str:
    match = re.search(
        rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+'
        r'content=(["\'])(.*?)\1',
        document,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(2).strip() if match else ""


def _profile(document: str, user: str) -> dict:
    for encoded in re.findall(r'\.push\(("(?:[^"\\]|\\.)*")\);', document):
        try:
            payload = json.loads(json.loads(encoded))
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(payload, dict):
            continue
        data = payload.get("data")
        if not isinstance(data, dict):
            continue
        profile = data.get("user")
        if (
            isinstance(profile, dict)
            and str(profile.get("profileUrl", "")).casefold()
            == f"/profile/{user}".casefold()
        ):
            return profile
    return {}


def _qtext(document: dict | None) -> str:
    if not document:
        return ""
    try:
        sections = json.loads(document["legacyJson"])["sections"]
        return "\n".join(
            "".join(span.get("text", "") for span in section.get("spans", []))
            for section in sections
        ).strip()
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError):
        return ""


def _values(values) -> list | None:
    values = list(dict.fromkeys(value for value in values if value))
    return values or None


def _extra(profile: dict) -> dict:
    extra = {}
    for key, field in (
        ("uid", "uid"),
        ("followers", "followerCount"),
        ("following", "followingCount"),
        ("answers", "numPublicAnswers"),
        ("questions", "numProfileQuestions"),
        ("posts", "postsCount"),
        ("content_views", "allTimePublicContentViews"),
        ("monthly_content_views", "lastMonthPublicContentViews"),
        ("verified", "isVerified"),
    ):
        extra[key] = profile.get(field)

    name = (profile.get("names") or [{}])[0]
    extra["first_name"] = name.get("givenName")
    extra["last_name"] = name.get("familyName")

    if created := profile.get("creationTime"):
        try:
            extra["joined"] = datetime.fromtimestamp(
                created / 1_000_000, timezone.utc
            ).isoformat()
        except (TypeError, ValueError, OSError, OverflowError):
            pass

    extra["credential"] = (profile.get("profileCredential") or {}).get("experience")
    extra["bio"] = _qtext(profile.get("descriptionQtextDocument"))

    for key, field, relation, fallback in (
        ("work", "workCredentials", "company", "companyName"),
        ("schools", "schoolCredentials", "school", "schoolName"),
        ("location", "locationCredentials", "location", "locationName"),
    ):
        extra[key] = _values(
            (item.get(relation) or {}).get("name") or item.get(fallback)
            for item in profile.get(field) or []
        )

    extra["topics"] = _values(
        (edge.get("node") or {}).get("name")
        for edge in (profile.get("expertiseTopicsConnection") or {}).get("edges", [])
    )

    extra["top_writer_years"] = _values(profile.get("topWriterYears") or [])
    extra["publishers"] = _values(
        item.get("publisherName") for item in profile.get("publishers") or []
    )

    return extra


def validate_quora(user: str) -> Result:
    encoded = quote(user, safe="")
    url = f"https://www.quora.com/profile/{encoded}"

    def process(response):
        document = response.text
        if response.status_code == 404 and '"rootProps": {"code": 404' in document:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        canonical = _meta(document, "og:url")
        if canonical.rstrip("/").rsplit("/", 1)[-1].casefold() != user.casefold():
            return Result.error("Profile resolved to a different username")
        if _meta(document, "og:type") != "profile":
            return Result.error("Missing Quora profile markers")

        profile = _profile(document, user)
        extra = _extra(profile)

        avatar = profile.get("profileImageUrl") or ""
        if "share_default_image" in avatar or "profile_default" in avatar:
            avatar = ""
        return Result.taken(extra=extra, media={"avatar": avatar})

    return generic_validate(url, process, show_url=url, follow_redirects=True)
