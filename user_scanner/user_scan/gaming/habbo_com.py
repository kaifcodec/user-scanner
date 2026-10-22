from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_habbo_com(user: str) -> Result:
    url = "https://www.habbo.com/api/public/users"
    show_url = f"https://www.habbo.com/profile/{user}"
    headers = {"Accept": "application/json"}

    def process(response):
        try:
            data = response.json()
        except ValueError:
            return Result.error(f"Unexpected non-JSON response: {response.status_code}")

        if response.status_code == 404 and data.get("error") == "not-found":
            return Result.available()

        if response.status_code != 200 or not data.get("uniqueId"):
            return Result.error(
                f"Unexpected response status or payload: {response.status_code}"
            )

        extra = {}
        media = {}

        if name := data.get("name"):
            extra["name"] = name
        if motto := data.get("motto"):
            extra["motto"] = motto
        if "online" in data:
            extra["online"] = data["online"]
        if member_since := data.get("memberSince"):
            extra["member_since"] = member_since
        if last_access := data.get("lastAccessTime"):
            extra["last_access"] = last_access
        if "profileVisible" in data:
            extra["profile_visible"] = data["profileVisible"]
        if "currentLevel" in data:
            extra["level"] = data["currentLevel"]
        if "totalExperience" in data:
            extra["experience"] = data["totalExperience"]
        if "starGemCount" in data:
            extra["star_gems"] = data["starGemCount"]
        if figure := data.get("figureString"):
            media["avatar"] = (
                "https://www.habbo.com/habbo-imaging/avatarimage"
                f"?figure={figure}&size=l&direction=2&head_direction=3&gesture=sml"
            )

        return Result.taken(extra=extra, media=media)

    return generic_validate(
        url,
        process,
        show_url=show_url,
        headers=headers,
        params={"name": user},
    )
