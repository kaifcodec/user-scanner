from user_scanner.core.orchestrator import Result, make_request
from user_scanner.core.helpers import get_random_user_agent


def validate_gravatar(user: str) -> Result:
    url = f"https://en.gravatar.com/{user}.json"
    show_url = f"https://gravatar.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json"
    }

    try:
        response = make_request(url, headers=headers)

        # 404 or string "User not found" indicates not available
        if response.status_code == 404 or "User not found" in response.text:
            return Result.available(url=show_url)

        if response.status_code == 200:
            data = response.json()
            extra = {}
            if "entry" in data and len(data["entry"]) > 0:
                entry = data["entry"][0]

                if entry.get("hash"):
                    extra["gravatar_id"] = entry["hash"]
                if entry.get("thumbnailUrl"):
                    extra["image"] = entry["thumbnailUrl"]
                if entry.get("preferredUsername"):
                    extra["username"] = entry["preferredUsername"]
                if entry.get("name", {}).get("formatted"):
                    extra["fullname"] = entry["name"]["formatted"]
                elif entry.get("displayName"):
                    extra["fullname"] = entry["displayName"]
                if entry.get("aboutMe"):
                    extra["bio"] = entry["aboutMe"]
                if entry.get("currentLocation"):
                    extra["location"] = entry["currentLocation"]

                emails = [y["value"] for y in entry.get("emails", [])]
                if emails:
                    extra["emails"] = ", ".join(emails)

                links = [y["url"] for y in entry.get("accounts", [])]
                links.extend([y["value"] for y in entry.get("urls", [])])
                if links:
                    extra["links"] = ", ".join(links)

                return Result.taken(extra=extra, url=show_url)

        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
