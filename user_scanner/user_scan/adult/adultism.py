from user_scanner.core.orchestrator import status_validate


def validate_adultism(user):
    url = f"https://www.adultism.com/profile/{user}"
    show_url = f"https://www.adultism.com/profile/{user}"

    return status_validate(url, 404, 200, show_url=show_url)
