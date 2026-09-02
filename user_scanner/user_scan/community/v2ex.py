import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_v2ex(user: str) -> Result:
    url = "https://www.v2ex.com/api/members/show.json"
    encoded_user = urllib.parse.quote(user)
    show_url = f"https://www.v2ex.com/u/{encoded_user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    params = {"username": user}

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("status") == "found" and data.get("username"):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if data.get("id") is not None:
                        extra["user_id"] = str(data["id"])
                    if data.get("tagline"):
                        extra["tagline"] = str(data["tagline"])
                    if data.get("bio"):
                        extra["bio"] = str(data["bio"])
                    if data.get("website"):
                        extra["website"] = str(data["website"])
                    if data.get("location"):
                        extra["location"] = str(data["location"])
                    if data.get("github"):
                        extra["github"] = str(data["github"])
                    if data.get("twitter"):
                        extra["twitter"] = str(data["twitter"])
                    if data.get("created"):
                        extra["joined"] = str(data["created"])

                    avatar = (
                        data.get("avatar_xxxlarge")
                        or data.get("avatar_xxlarge")
                        or data.get("avatar_xlarge")
                        or data.get("avatar_large")
                    )
                    if avatar:
                        media["avatar"] = str(avatar)

                    return Result.taken(url=show_url, extra=extra, media=media)

                if data.get("status") == "error":
                    return Result.available(url=show_url)
            except Exception:
                pass
            return Result.error("V2EX 200 response missing valid member payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, params=params, follow_redirects=True)
