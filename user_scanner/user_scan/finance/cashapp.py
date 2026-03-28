from user_scanner.core.orchestrator import status_validate

def validate_cashapp(user):
    
    url = f"https://cash.app/${user}"
    show_url = f"https://cash.app/${user}"

    return status_validate(url, 404, 200, show_url=show_url)
