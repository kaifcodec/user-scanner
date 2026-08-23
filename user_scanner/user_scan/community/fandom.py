import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_fandom(user: str) -> Result:
    """Validate a username on Fandom (fandom.com)."""
    url = "https://community.fandom.com/api.php"
    show_url = f"https://community.fandom.com/wiki/User:{user}"
    params = {
        "action": "query",
        "list": "users",
        "ususers": user,
        "usprop": "registration|gender|editcount|groups",
        "format": "json",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + Fandom API response
        if response.status_code == 200 and "users" in response.text:
            try:
                data = json.loads(response.text)
                users = data.get("query", {}).get("users", [])

                if not users:
                    return Result.available(url=show_url)

                user_data = users[0]

                # Explicit check for Fandom MediaWiki "missing" flag
                if "missing" in user_data:
                    return Result.available(url=show_url)

                if "userid" in user_data:
                    extra = {}
                    if name := user_data.get("name"):
                        extra["name"] = str(name).strip()
                    if user_id := user_data.get("userid"):
                        extra["user_id"] = str(user_id)
                    if edit_count := user_data.get("editcount"):
                        extra["edit_count"] = str(edit_count)
                    if reg := user_data.get("registration"):
                        extra["registered"] = str(reg).strip()
                    if groups := user_data.get("groups"):
                        filtered_groups = [g for g in groups if g != "*"]
                        if filtered_groups:
                            extra["groups"] = ", ".join(filtered_groups)

                    return Result.taken(extra=extra, url=show_url)
            except Exception:
                return Result.error("Failed to parse Fandom API response", url=show_url)

        # 3. Graceful error for unexpected status codes or unhandled responses (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(
        url, process, headers=headers, show_url=show_url,
        follow_redirects=True, params=params,
    )
