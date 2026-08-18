import json
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_bio_site(user: str) -> Result:
    """Validate a username on Bio Site (bio.site)."""
    url = f"https://bio.site/{user}"
    show_url = f"https://bio.site/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def process(response):
        if response.status_code == 200 and "bio.site" in response.text.lower():
            state_match = re.search(
                r"window\.initial_state=({[\s\S]+?});\s*window\.additional",
                response.text,
            )
            if state_match:
                try:
                    state_data = json.loads(state_match.group(1))
                    metadata = state_data.get("metadata", {})
                    header = state_data.get("header", {})

                    handle = metadata.get("handle")
                    if handle and str(handle).lower() == user.lower():
                        extra = {}
                        media = {}
                        if name := header.get("name"):
                            extra["name"] = str(name).strip()
                        if bio := header.get("bio"):
                            extra["bio"] = str(bio).strip()
                        if photo := (header.get("profilePhoto") or header.get("profile_photo")):
                            media["avatar"] = str(photo).strip()

                        return Result.taken(extra=extra, media=media, url=show_url)
                except Exception:
                    pass
            return Result.available(url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
