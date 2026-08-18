import json
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_hive_blog(user: str) -> Result:
    """Validate a username on Hive Blog (hive.blog)."""
    url = f"https://hive.blog/@{user}"
    show_url = f"https://hive.blog/@{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit check for available / not-found state (HTTP 404 or explicit title marker)
        if response.status_code == 404 or "user not found - hive" in response_text_lower or "user not found" in response_text_lower:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + site marker
        if response.status_code == 200 and "hive" in response_text_lower:
            script_match = re.search(
                r'<script[^>]*>(\{"community":[\s\S]+?)</script>',
                response.text,
            )
            if script_match:
                try:
                    data = json.loads(script_match.group(1))
                    profiles = data.get("userProfiles", {}).get("profiles", {})
                    user_key = user.lower()

                    if user_key in profiles and isinstance(profiles[user_key], dict):
                        user_info = profiles[user_key]
                        metadata = user_info.get("metadata", {}).get("profile", {})
                        stats = user_info.get("stats", {})

                        extra = {}
                        media = {}
                        if name := metadata.get("name"):
                            if str(name).strip():
                                extra["name"] = str(name).strip()
                        if about := metadata.get("about"):
                            if str(about).strip():
                                extra["about"] = str(about).strip()
                        if website := metadata.get("website"):
                            if str(website).strip():
                                extra["website"] = str(website).strip()
                        if location := metadata.get("location"):
                            if str(location).strip():
                                extra["location"] = str(location).strip()
                        if avatar := metadata.get("profile_image"):
                            if str(avatar).strip():
                                media["avatar"] = str(avatar).strip()

                        if followers := stats.get("followers"):
                            extra["followers"] = str(followers)
                        if following := stats.get("following"):
                            extra["following"] = str(following)
                        if post_count := user_info.get("post_count"):
                            extra["post_count"] = str(post_count)

                        return Result.taken(extra=extra, media=media, url=show_url)
                except Exception:
                    return Result.error("Failed to parse userProfiles JSON on Hive Blog", url=show_url)
            return Result.error("Could not find userProfiles script tag on Hive Blog", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
