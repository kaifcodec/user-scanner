from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_boot_dev(user: str) -> Result:
    url = f"https://api.boot.dev/v1/users/public/{quote(user.lower(), safe='')}"
    show_url = f"https://boot.dev/u/{user}"

    def process(response):
        data = response.json()

        if response.status_code == 404 and data.get("error") == "User not found":
            return Result.available()
        profile = data.get("data", {})
        if (
            response.status_code == 200
            and data.get("status") == "success"
            and profile.get("handle", "").lower() == user.lower()
        ):
            linkedin = profile.get("linkedinURL")
            if linkedin and linkedin.startswith(("linkedin.com/", "www.linkedin.com/")):
                linkedin = f"https://{linkedin}"

            return Result.taken(
                extra={
                    "first_name": profile.get("firstName"),
                    "last_name": profile.get("lastName"),
                    "handle": profile.get("handle"),
                    "bio": profile.get("bio"),
                    "location": profile.get("location"),
                    "github": profile.get("githubHandle"),
                    "twitter": profile.get("twitterHandle"),
                    "linkedin": linkedin,
                    "website": profile.get("websiteURL"),
                    "user_id": profile.get("uuid"),
                    "joined": profile.get("createdAt"),
                    "updated": profile.get("updatedAt"),
                    "level": profile.get("level"),
                    "xp": profile.get("xp"),
                    "role": profile.get("role"),
                    "is_member": profile.get("isMember"),
                    "gems": profile.get("gems"),
                    "xp_for_level": profile.get("xpForLevel"),
                    "xp_total_for_level": profile.get("xpTotalForLevel"),
                },
                media={"avatar": profile.get("profileImageURL")},
            )
        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
