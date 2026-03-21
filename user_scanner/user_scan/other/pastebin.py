from user_scanner.core.orchestrator import status_validate

def validate_pastebin(user):
    
    url = f"https://pastebin.com/u/{user}"
    show_url = f"https://pastebin.com/u/{user}"

    return status_validate(url, 404, 200, show_url=show_url)
