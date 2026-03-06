from user_scanner.core.orchestrator import status_validate

def validate_destream(user):
    url = f"https://api.destream.net/siteapi/v2/live/details/{user}"
    show_url = f"https://destream.net/live/{user}"

    return status_validate(url, 404, 200, show_url=show_url)
