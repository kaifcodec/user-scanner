from user_scanner.core.orchestrator import status_validate


def validate_ameblo(user):
    url = f"https://ameblo.jp/{user}"
    show_url = f"https://ameblo.jp/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
