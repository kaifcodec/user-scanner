import json
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import quote, urlsplit

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import iter_next_app_flight_chunks
from user_scanner.core.result import Result

NOT_FOUND = "<title>404: Страница не найдена</title>"


def validate_weblancer(user: str) -> Result:
    username = user.strip()
    url = f"https://www.weblancer.net/users/{quote(username, safe='')}/"

    def process(response):
        if response.status_code == 404 and NOT_FOUND in response.text:
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        profile = _profile(response.text, username)
        if profile is None:
            return Result.error("Weblancer profile markers were missing")

        description = _flight_text(response.text, profile.get("description"))
        extra = {
            "id": profile.get("id"),
            "first_name": profile.get("first_name"),
            "last_name": profile.get("last_name"),
            "bio": _text(description),
            "social_links": _social_links(description) or None,
            "gender": profile.get("gender"),
            "birthday": profile.get("birthday"),
            "title": profile.get("title"),
            "country": (profile.get("country") or {}).get("name"),
            "city_id": profile.get("city_id"),
            "timezone": _utc_offset(profile.get("time_zone")),
            "account_type": profile.get("account_type"),
            "is_customer": profile.get("isCustomer"),
            "is_freelancer": profile.get("isFreelancer"),
            "blocked": profile.get("blocked"),
            "block_reason": profile.get("block_reason"),
            "no_index": profile.get("noIndex"),
            "settings": profile.get("settings"),
            "verified": profile.get("verified"),
            "online": profile.get("online"),
            "freelancer_rating": profile.get("freelancer_rating"),
            "customer_rating": profile.get("customer_rating"),
            "reviews_per_year": profile.get("reviewsPerYear"),
            "jobs": profile.get("jobCount"),
            "portfolio": profile.get("portfolio_count"),
            "services": profile.get("services_count"),
            "projects": profile.get("projects_count"),
            "contests": profile.get("contests_count"),
            "vacancies": profile.get("vacancies_count"),
            "created_at": _iso(profile.get("created_time")),
            "last_online_at": _iso(profile.get("last_online_time")),
            "skills": [
                tag["name"]
                for tag in profile.get("tagList") or []
                if isinstance(tag, dict) and isinstance(tag.get("name"), str)
            ]
            or None,
        }
        for label, value in (
            ("reviews", profile.get("reviews_count")),
            ("freelancer_reviews", profile.get("freelancer_reviews_count")),
            ("customer_reviews", profile.get("customer_reviews_count")),
        ):
            extra.update(_review_breakdown(label, value))
        extra.update(_statistics(profile))
        userpic = profile.get("userpic_file")
        media = {
            "avatar": f"https://st.weblancer.net/download/{quote(userpic, safe='')}"
            if isinstance(userpic, str) and userpic
            else None
        }
        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process)


def _profile(document: str, username: str) -> dict | None:
    decoder = json.JSONDecoder()
    for chunk in iter_next_app_flight_chunks(document):
        start = 0
        while (marker := chunk.find('"user":', start)) >= 0:
            start = marker + len('"user":')
            try:
                candidate = decoder.raw_decode(chunk[start:])[0]
            except json.JSONDecodeError:
                continue
            if (
                isinstance(candidate, dict)
                and isinstance(candidate.get("login"), str)
                and candidate["login"].casefold() == username.casefold()
            ):
                return candidate
    return None


def _flight_text(document: str, value: object) -> str | None:
    if not isinstance(value, str) or not value.startswith("$"):
        return value if isinstance(value, str) else None

    pattern = re.compile(rf"(?m)^{re.escape(value[1:])}:T([0-9a-f]+),")
    for chunk in iter_next_app_flight_chunks(document):
        if match := pattern.search(chunk):
            size = int(match.group(1), 16)
            try:
                return chunk[match.end() :].encode()[:size].decode()
            except UnicodeDecodeError:
                return None
    return None


def _text(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _social_links(value: str | None) -> list[str]:
    links = []
    for href in re.findall(r'<a\b[^>]*\bhref=["\']([^"\']+)', value or "", re.IGNORECASE):
        href = unescape(href)
        href = f"https:{href}" if href.startswith("//") else href
        if urlsplit(href).scheme in {"http", "https"} and href not in links:
            links.append(href)
    return links


def _review_breakdown(label: str, value: object) -> dict[str, int]:
    try:
        positive, negative = (int(count) for count in str(value).split("|", 1))
    except ValueError:
        return {}
    return {
        label: positive + negative,
        f"{label}_positive": positive,
        f"{label}_negative": negative,
    }


def _utc_offset(value: object) -> str | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return timezone(timedelta(hours=value)).tzname(None)
    except (OverflowError, ValueError):
        return None


def _statistics(profile: dict) -> dict:
    statistics: dict[str, object] = {}
    for prefix, value in (
        ("freelancer", profile.get("freelancer_stats")),
        ("customer", profile.get("customer_stats")),
    ):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict):
            statistics.update({f"{prefix}_{key}": item for key, item in value.items()})

    rating = profile.get("rating")
    if not isinstance(rating, dict):
        return statistics

    total = rating.get("total")
    if isinstance(total, dict):
        statistics.update(
            {
                "overall_rank": total.get("position"),
                "overall_rank_rating": total.get("rating"),
                "overall_rank_jobs": total.get("jobs_count"),
                "ranking_updated_at": _iso(total.get("updated_time")),
            }
        )

    return statistics


def _iso(value: object) -> str | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec="seconds")
    except (OSError, OverflowError, ValueError):
        return None
