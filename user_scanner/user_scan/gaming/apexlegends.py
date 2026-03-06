from user_scanner.core.orchestrator import status_validate


def validate_apexlegends(user):
    url = f"https://api.tracker.gg/api/v2/apex/standard/profile/origin/{user}"
    show_url = f"https://apex.tracker.gg/apex/profile/origin/{user}/overview"

    headers = {
        "Accept-Language": "en-US,en;q=0.5",
        "Origin": "https://apex.tracker.gg",
        "Referer": "https://apex.tracker.gg/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    }

    return status_validate(url, 404, 200, show_url=show_url, headers=headers)
