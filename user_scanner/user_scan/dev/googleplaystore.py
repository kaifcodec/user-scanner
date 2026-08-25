from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_googleplaystore(user: str) -> Result:
    url = "https://play.google.com/store/apps/developer"
    display_url = f"https://play.google.com/store/apps/developer?id={user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = make_request(
            url, params={"id": user}, headers=headers, follow_redirects=True)

        if response.status_code == 200:
            return Result.taken(url=display_url)
        elif response.status_code == 404:
            return Result.available(url=display_url)

        return Result.error(f"Unexpected response status: {response.status_code}", url=display_url)

    except Exception as e:
        return Result.error(e, url=display_url)
