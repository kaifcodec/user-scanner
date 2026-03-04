from user_scanner.core.orchestrator import status_validate


def validate_devto(user):
    url = f"https://dev.to/{user}"
    show_url = f"https://dev.to/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
