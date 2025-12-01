from ..core.orchestrator import status_validate


def validate_facebook(user: str) -> int:
    """
    Checks if a Facebook username is available.

    Strategy:
    - Facebook profile URLs follow the pattern: https://www.facebook.com/<username>
    - Existing usernames typically return HTTP 200.
    - Non-existing usernames are expected to return HTTP 404 or a similar not-found status.
    - We rely on HTTP status codes using status_validate.
    """
    url = f"https://www.facebook.com/{user}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    }

    # 404 -> available, 200 -> taken
    return status_validate(url, 404, 200, headers=headers, follow_redirects=True)


