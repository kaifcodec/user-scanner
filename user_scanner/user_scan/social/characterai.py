import json
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_characterai(user: str) -> Result:
    url = "https://character.ai/api/trpc/social.publicProfile"
    profile_url = f"https://character.ai/profile/{quote(user, safe='')}"
    params = {"input": json.dumps({"json": {"username": user}})}

    def process(response):
        try:
            data = response.json()
        except ValueError:
            return Result.error("Could not read Character.AI profile data")

        error = data.get("error", {}).get("json", {}).get("data", {})
        upstream = error.get("axiosErrorData", {})
        if (
            response.status_code == 500
            and error.get("path") == "social.publicProfile"
            and upstream.get("upstreamStatus") == 404
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        profile = data.get("result", {}).get("data", {}).get("json")
        if not isinstance(profile, dict) or profile.get("username") != user:
            return Result.error("Character.AI profile data was missing")

        characters = profile.get("characters")
        extra = {
            "fullname": profile.get("name"),
            "bio": profile.get("bio"),
            "followers": profile.get("num_followers"),
            "following": profile.get("num_following"),
            "characters": len(characters) if isinstance(characters, list) else None,
            "subscription": profile.get("subscription_type"),
        }
        if isinstance(characters, list):
            created = [character.get("created") for character in characters]
            updated = [character.get("updated") for character in characters]
            extra.update(
                {
                    "user_id": characters[0].get("user_id") if characters else None,
                    "interactions": sum(
                        character.get("participant__num_interactions") or 0
                        for character in characters
                    ),
                    "upvotes": sum(
                        character.get("upvotes") or 0 for character in characters
                    ),
                    "first_character_created": min(created, default=None),
                    "last_character_updated": max(updated, default=None),
                }
            )
        avatar = profile.get("avatar_file_name")
        media = (
            {"avatar": f"https://characterai.io/i/200/static/avatars/{avatar}?anim=0"}
            if avatar
            else {}
        )
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, params=params, show_url=profile_url)
