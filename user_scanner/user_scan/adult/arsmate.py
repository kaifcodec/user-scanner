from datetime import datetime, timezone

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_arsmate(user: str) -> Result:
    url = f"https://arsmate.com/api/creators/{user}"
    show_url = f"https://arsmate.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response):
        if response.status_code == 200 or response.status_code == 404:
            try:
                data = response.json()
            except Exception:
                return Result.error("Unexpected response body, report it via GitHub issues")
            if data.get("error") is True:
                return Result.available()
            creator = data.get("creator")
            if not isinstance(creator, dict) or "username" not in creator:
                return Result.error("Unexpected API response body, report it via GitHub issues")
            extra = {}
            media = {}
            if name := creator.get("name"): extra["name"] = name
            if username := creator.get("username"): extra["username"] = username
            if bio := creator.get("about"): extra["bio"] = bio
            if profession := creator.get("profession"): extra["profession"] = profession
            if website := creator.get("website"): extra["links"] = website
            extra["verified"] = bool(creator.get("isVerified"))
            if birthdate := creator.get("birthdate"): extra["birth_date"] = birthdate
            if country := creator.get("countryId"): extra["country"] = country
            if created_at := creator.get("createdAt"):
                extra["joined"] = datetime.fromtimestamp(
                    datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp(),
                    timezone.utc
                ).strftime("%Y-%m-%d")
            stats = creator.get("stats") or {}
            if subscribers := stats.get("subscribers"): extra["subscribers"] = str(subscribers)
            if posts := stats.get("posts"): extra["posts"] = str(posts)
            if photos := stats.get("photos"): extra["photos"] = str(photos)
            if videos := stats.get("videos"): extra["videos"] = str(videos)
            if likes := stats.get("likes"): extra["likes"] = str(likes)
            if social := creator.get("social"):
                links = [v for v in social.values() if isinstance(v, str) and v]
                if links:
                    extra["social"] = " ".join(links)
            if avatar := creator.get("avatar"): media["avatar"] = avatar
            if cover := creator.get("cover"): media["banner"] = cover
            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
