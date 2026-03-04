from user_scanner.core.orchestrator import status_validate


def validate_patreon(user):
    url = f"https://www.patreon.com/{user}"
    show_url = f"https://www.patreon.com/{user}"

    return status_validate(
        url, 404, 200, show_url=show_url, timeout=15.0, follow_redirects=True
    )
