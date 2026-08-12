import json
import re

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_tinder(user: str) -> Result:
    url = f"https://tinder.com/@{user}"

    def process(response: httpx.Response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        data = _page_data(response.text)
        if data is None:
            return Result.error("Profile response contained malformed page data")

        profile = data.get("webProfile")
        if not isinstance(profile, dict):
            return Result.error("Profile response contained no web profile data")
        if not profile:
            return Result.available()

        profile_user = profile.get("username")
        if not isinstance(profile_user, str):
            return Result.error("Profile response was ambiguous")
        if profile_user.casefold() != user.casefold():
            return Result.error("Profile payload does not match the requested handle")

        details = profile.get("user")
        if not isinstance(details, dict):
            return Result.error("Profile payload contained no user data")

        extra, media = _extract(details)
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url)


def _page_data(text: str) -> dict | None:
    match = re.search(
        r"window\.__data\s*=\s*(\{.*?\})\s*;</script>", text, re.DOTALL
    )
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _extract(details: dict) -> tuple[dict, dict]:
    extra: dict[str, object] = {
        "name": details.get("name"),
        "birth_date": details.get("birth_date"),
        "user_id": details.get("_id"),
    }
    if isinstance(birth_date := extra["birth_date"], str):
        extra["birth_date"] = birth_date.partition("T")[0]

    badges = [
        badge["type"].strip()
        for badge in details.get("badges") or []
        if isinstance(badge, dict)
        and isinstance(badge.get("type"), str)
        and badge["type"].strip()
    ]
    if badges:
        extra["badges"] = badges

    jobs = details.get("jobs") or []
    job = (
        jobs[0]
        if isinstance(jobs, list) and jobs and isinstance(jobs[0], dict)
        else {}
    )
    company = job.get("company") or {}
    title = job.get("title") or {}
    extra["company"] = company.get("name") if isinstance(company, dict) else None
    extra["job_title"] = title.get("name") if isinstance(title, dict) else None

    schools = details.get("schools") or []
    school = (
        schools[0]
        if isinstance(schools, list) and schools and isinstance(schools[0], dict)
        else {}
    )
    extra["school"] = school.get("name")

    media = {
        f"photo_{index}": photo["url"]
        for index, photo in enumerate(details.get("photos") or [], 1)
        if isinstance(photo, dict)
        and isinstance(photo.get("url"), str)
    }
    return extra, media
