from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.result import Result, Status


def validate_quizlet(user: str) -> Result:
    url = f"https://quizlet.com/user/{user}/sets"

    def process(response):
        html = response.text

        if "Captcha Challenge" in html or "has been denied" in html or "_pxVid" in html:
            return Result.error("Blocked by Quizlet bot challenge")

        if response.status_code == 404:
            data = parse_next_pages_data(html) or {}
            page_props = data.get("props", {}).get("pageProps", {})
            if data.get("page") == "/_error" and page_props.get("statusCode") == 404:
                return Result.available()
            return Result.error("Unrecognized Quizlet not-found response")

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        data = parse_next_pages_data(html)
        if not data:
            return Result.error("Quizlet profile payload was missing")

        page_props = data.get("props", {}).get("pageProps", {})
        account = page_props.get("user")
        if not isinstance(account, dict):
            return Result.error("Quizlet profile gave no user record")

        if str(account.get("username", "")).lower() != user.lower():
            return Result.error("Quizlet profile marker did not match target")

        extra = {}
        media = {}

        fullname = " ".join(
            part for part in (account.get("firstName"), account.get("lastName")) if part
        ).strip()
        if fullname:
            extra["fullname"] = fullname
        if account.get("timeZone"):
            extra["time_zone"] = account["timeZone"]

        counts = {
            "uploads": page_props.get("numCreated"),
            "classes": page_props.get("numClasses"),
            "folders": page_props.get("numFolders"),
        }
        for key, value in counts.items():
            if isinstance(value, int):
                extra[key] = value

        if isinstance(page_props.get("isTopCreator"), bool) and page_props["isTopCreator"]:
            extra["top_creator"] = True

        if account.get("_imageUrl"):
            media["avatar"] = str(account["_imageUrl"])

        return Result.taken(extra=extra, media=media)

    return _fallback_profiles(url, process)


def _fallback_profiles(url: str, process) -> Result:
    profiles = ("firefox", "safari")
    for index, profile in enumerate(profiles):
        result = impersonate_validate(url, process, show_url=url, impersonate=profile)
        blocked = result.status is Status.ERROR and any(
            word in result.get_reason().lower()
            for word in ("challenge", "denied")
        )
        if not blocked or index == len(profiles) - 1:
            return result
    return result
