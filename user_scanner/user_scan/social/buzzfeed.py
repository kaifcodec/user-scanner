from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.result import Result


def validate_buzzfeed(user: str) -> Result:
    url = f"https://www.buzzfeed.com/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code != 200:
            return Result.error(f"HTTP {r.status_code}")

        data = parse_next_pages_data(r.text) or {}
        page_props = data.get("props", {}).get("pageProps", {})
        user_data = page_props.get("user") or {}

        # Section pages (/quizzes, /tasty, /search) answer 200 with the same
        # shell and no user node, so a bare 200 is not an account.
        if not user_data:
            return Result.error("200 response with no profile data")

        extra, media = _extract(page_props, user_data)
        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, allow_redirects=True)

def _extract(page_props: dict, user_data: dict) -> tuple[dict, dict]:
    extra: dict = {}
    media: dict = {}

    if display_name := user_data.get("displayName"):
        extra["display_name"] = display_name
    if bio := user_data.get("bio"):
        extra["bio"] = bio

    if img := user_data.get("image"):
        if not img.startswith("http"):
            img = f"https://img.buzzfeed.com/buzzfeed-static{img}"
        media["avatar_url"] = img

    if member_since := user_data.get("memberSince"):
        try:
            joined = datetime.fromtimestamp(int(member_since), tz=timezone.utc)
            extra["joined"] = joined.strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            pass

    if page_props.get("points") is not None:
        extra["points"] = int(page_props["points"])
    if page_props.get("buzz_count") is not None:
        extra["posts"] = int(page_props["buzz_count"])

    links = [s["url"] for s in user_data.get("social", []) if s.get("url")]
    if links:
        extra["links"] = links

    return extra, media
