from user_scanner.core.orchestrator import status_validate


def validate_huggingface(user):
    url = f"https://huggingface.co/{user}"
    show_url = f"https://huggingface.co/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
