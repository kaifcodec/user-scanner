from user_scanner.core.orchestrator import status_validate


def validate_buymeacoffee(user):
    url = f"https://buymeacoffee.com/{user}"
    show_url = f"https://buymeacoffee.com/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
