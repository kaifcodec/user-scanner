from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_daily_dev(user):
    url = f"https://daily.dev/{user}"
    show_url = url

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()

        next_data = parse_next_pages_data(response.text)
        if next_data is None:
            return Result.error(
                "Could not read __NEXT_DATA__ payload, report it via GitHub issues."
            )

        page_props = next_data.get("props", {}).get("pageProps", {})
        user_data = page_props.get("user")
        user_stats = page_props.get("userStats", {})

        if isinstance(user_data, dict) and user_data.get("id"):
            extra = {}
            if user_data.get("name"):
                extra["name"] = user_data.get("name")
            if user_data.get("bio"):
                extra["bio"] = user_data.get("bio")
            if user_data.get("reputation") is not None:
                extra["reputation"] = user_data.get("reputation")
            if user_data.get("createdAt"):
                extra["joined"] = user_data.get("createdAt")
            if isinstance(user_stats, dict):
                if user_stats.get("numFollowers") is not None:
                    extra["followers"] = user_stats.get("numFollowers")
                if user_stats.get("numFollowing") is not None:
                    extra["following"] = user_stats.get("numFollowing")
            return Result.taken(extra=extra)

        return Result.available()

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)
