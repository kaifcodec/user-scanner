from user_scanner.core.orchestrator import status_validate


def validate_coderlegion(user):
    url = f"https://coderlegion.com/user/{user}"
    show_url = f"https://coderlegion.com/user/{user}"

    return status_validate(url, 404, 200, show_url=show_url, timeout=15.0)
