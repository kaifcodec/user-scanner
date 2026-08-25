import json

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def validate_atlassian(email: str) -> Result:
    """Validate whether an email is registered on Atlassian (Jira, Confluence, Bitbucket, Trello)."""
    url = "https://id.atlassian.com/rest/check-username"
    show_url = "https://id.atlassian.com"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://id.atlassian.com/login",
        "Accept-Language": "en-US,en;q=0.9",
    }
    payload = json.dumps({"username": email})

    try:
        response = await impersonate_request_async(
            url,
            method="POST",
            data=payload,
            headers=headers,
            impersonate="chrome",
        )

        if response.status_code == 403:
            return Result.error("Caught by WAF (403)", url=show_url)

        if response.status_code == 429:
            return Result.error("Rate limited by Atlassian (429)", url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

        data = response.json()
        if not isinstance(data, dict):
            return Result.error("Unexpected response body format", url=show_url)

        action = data.get("action")
        if action == "signup":
            return Result.available(url=show_url)

        if action in ("no_action", "redirect"):
            extra = {}
            if action == "redirect":
                extra["auth_type"] = "SSO / SAML"
                if redirect_type := data.get("redirect_type"):
                    extra["sso_type"] = redirect_type
            elif action == "no_action":
                extra["auth_type"] = "Password / Social"

            return Result.taken(extra=extra, url=show_url)

        return Result.error(f"Unknown action response: {action}", url=show_url)

    except Exception as e:
        return Result.error(f"Unexpected exception: {e}", url=show_url)
