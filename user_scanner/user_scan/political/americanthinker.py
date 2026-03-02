from user_scanner.core.orchestrator import status_validate


def validate_americanthinker(user):
    url = f"https://www.americanthinker.com/author/{user}/"
    show_url = url

    return status_validate(url, 404, 200, show_url=show_url)
