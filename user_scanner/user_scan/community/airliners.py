from user_scanner.core.orchestrator import status_validate


def validate_airliners(user):
    url = f"https://www.airliners.net/user/{user}/profile"
    show_url = f"https://www.airliners.net/user/{user}/profile"

    return status_validate(url, 404, 200, show_url=show_url)
