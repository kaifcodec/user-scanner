from user_scanner.core.orchestrator import status_validate


def validate_minecraft(user):
    url = f"https://api.mojang.com/minecraft/profile/lookup/name/{user}"
    show_url = f"https://namemc.com/profile/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
