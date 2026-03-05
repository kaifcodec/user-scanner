from user_scanner.core.orchestrator import status_validate

def validate_cropty(user):
    url = f"https://api.cropty.io/v1/auth/{user}"
    show_url = "https://www.cropty.io"

    return status_validate(url, 404, 200, show_url=show_url)
