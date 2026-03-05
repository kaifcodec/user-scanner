from user_scanner.core.orchestrator import status_validate


def validate_gpodder_net(user):
    url = f"https://gpodder.net/user/{user}/"
    show_url = f"https://gpodder.net/user/{user}/"

    return status_validate(url, 404, 200, show_url=show_url)
