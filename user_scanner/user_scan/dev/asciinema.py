from user_scanner.core.orchestrator import status_validate

def validate_asciinema(user):
    url = f"https://asciinema.org/~{user}"
    show_url = f"https://asciinema.org/~{user}"

    return status_validate(url, 404, 200, show_url=show_url)
