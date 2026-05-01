from user_scanner.core.orchestrator import status_validate


def validate_vk(user):
    url = f"https://www.vk.com/{user}"
    show_url = f"https://www.vk.com/{user}"

    return status_validate(url, 404, 200, show_url=show_url)