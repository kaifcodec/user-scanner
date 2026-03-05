from user_scanner.core.orchestrator import status_validate


def validate_kaggle(user):
    url = f"https://www.kaggle.com/{user}"
    show_url = f"https://www.kaggle.com/{user}"

    return status_validate(url, 404, 200, show_url=show_url, follow_redirects=True)
