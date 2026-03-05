from user_scanner.core.orchestrator import status_validate
from user_scanner.core.result import Result


def validate_linkedin(user: str) -> Result:
    # LinkedIn whitelists social media crawler bots for link previews,
    # bypassing the anti-bot 999 response that blocks regular user agents.
    # Note: bulk scanning may trigger rate limiting (999) after ~3 rapid requests.
    url = f"https://www.linkedin.com/in/{user}"
    show_url = f"https://www.linkedin.com/in/{user}/"

    headers = {
        "User-Agent": "Twitterbot/1.0",
    }

    return status_validate(
        url, available=404, taken=[200, 301], show_url=show_url,
        headers=headers, follow_redirects=False
    )
