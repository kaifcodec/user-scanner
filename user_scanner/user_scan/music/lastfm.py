from user_scanner.core.orchestrator import status_validate


def validate_lastfm(user):
    url = f"https://www.last.fm/user/{user}"
    show_url = f"https://www.last.fm/user/{user}"

    return status_validate(url, 404, 200, show_url=show_url)
