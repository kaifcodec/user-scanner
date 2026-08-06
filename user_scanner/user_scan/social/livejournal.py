import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

# The journal subdomain answers a ~750 KB page and stalls Python's TLS stack;
# the profile page carries the same Site.journal payload and always resolves.
PROFILE_URL = "https://www.livejournal.com/profile/"
JOURNAL_RE = re.compile(r"Site\.journal\s*=\s*(\{.+?\});")
NOT_FOUND_MARKER = "The page was not found!"


def validate_livejournal(user: str) -> Result:
    show_url = f"https://{user}.livejournal.com"

    def process(response):
        if response.status_code == 404 and NOT_FOUND_MARKER in response.text:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        journal = _journal(response.text)
        if not journal:
            return Result.error("200 response with no journal data")

        # Guard against the generic profile shell: only the requested journal's
        # own page echoes its username back.
        if str(journal.get("display_username", "")).lower() != user.lower():
            return Result.error("200 response for a different journal")

        return Result.taken(extra=_extract(journal), media=_media(journal))

    return impersonate_validate(
        PROFILE_URL, process, params={"user": user}, show_url=show_url
    )


def _journal(body: str) -> dict:
    match = JOURNAL_RE.search(body)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract(journal: dict) -> dict:
    extra: dict = {}

    if uid := journal.get("id"):
        extra["uid"] = uid
    if name := journal.get("display_username"):
        extra["name"] = name
    if subtitle := journal.get("journal_subtitle"):
        extra["subtitle"] = subtitle
    if url := journal.get("journal_url"):
        extra["journal_url"] = url

    extra["type"] = _account_type(journal)
    if journal.get("is_paid"):
        extra["is_paid"] = True

    return extra


def _account_type(journal: dict) -> str:
    if journal.get("is_syndicated"):
        return "syndicated feed"
    if journal.get("is_news"):
        return "news"
    return "personal" if journal.get("is_personal") else "community"


def _media(journal: dict) -> dict:
    userhead = journal.get("userhead_url")
    return {"userhead": userhead} if userhead else {}
