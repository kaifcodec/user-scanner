from user_scanner.core.orchestrator import generic_validate, status_validate, make_request
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


def validate_roblox(user: str) -> Result:
    url = "https://users.roblox.com/v1/usernames/users"
    show_url = "https://roblox.com"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    def process(response):
        if response.status_code == 429:
            return Result.error("Too many requests")

        if response.status_code == 200:
            try:
                data = response.json().get("data", [])
                if data:
                    entry = data[0]
                    uid = entry.get("id")
                    extra = {
                        "display name": entry.get("displayName"),
                        "uid": uid,
                        "is verified": entry.get("hasVerifiedBadge"),
                    }
                    if uid:
                        try:
                            detail_url = f"https://users.roblox.com/v1/users/{uid}"
                            detail_response = make_request(detail_url, follow_redirects=True)
                            if detail_response.status_code == 200:
                                details = detail_response.json()
                                if desc := details.get("description"): extra["bio"] = desc
                                if created := details.get("created"): extra["created"] = created
                                if details.get("isBanned"): extra["banned"] = "Yes"
                        except Exception:
                            pass
                    return Result.taken(extra=extra)
            except Exception:
                pass
            return Result.available()

        if response.status_code == 400:
            return Result.error("Invalid username")

        return Result.available()

    result = generic_validate(
        url,
        process,
        method="POST",
        json={"usernames": [user], "excludeBannedUsers": False},
        headers=headers,
        follow_redirects=True
    )

    if result.get_reason() != "Too many requests":
        return result

    # If rate limited, uses a simple status validation
    fallback_url = f"https://www.roblox.com/user.aspx?username={user}"

    return status_validate(
        fallback_url, 404, [200, 302], show_url=show_url, follow_redirects=True
    )
