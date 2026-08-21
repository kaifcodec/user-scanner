import json
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_ifunny(user: str) -> Result:
    """Validate a username on iFunny (ifunny.co)."""
    url = f"https://ifunny.co/user/{user}"
    show_url = f"https://ifunny.co/user/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or explicit 404 title)
        if (
            response.status_code == 404
            or "404 - page not found" in response_text_lower
            or "user not found" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and "ifunny" in response_text_lower:
            extra = {"username": user}
            media = {}

            state_match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", response.text)
            if state_match:
                try:
                    state_data = json.loads(state_match.group(1))
                    user_data = state_data.get("user", {}) or state_data.get("profile", {})
                    if nick := user_data.get("nick"):
                        extra["name"] = str(nick).strip()
                    if subscribers := (user_data.get("subscribers_count") or user_data.get("num_subscribers")):
                        extra["subscribers"] = str(subscribers)
                    if avatar := (user_data.get("photo_url") or user_data.get("avatar_url")):
                        media["avatar"] = str(avatar).strip()
                except Exception:
                    pass

            og_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text, re.IGNORECASE)
            if og_title_match and "name" not in extra:
                og_name = og_title_match.group(1).replace(" on iFunny", "").replace(" | iFunny", "").strip()
                if og_name and og_name.lower() != "ifunny":
                    extra["name"] = og_name

            og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text, re.IGNORECASE)
            if og_img_match and "avatar" not in media:
                img_url = og_img_match.group(1).strip()
                if img_url and "ifunny_logo" not in img_url.lower():
                    media["avatar"] = img_url

            return Result.taken(extra=extra, media=media, url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
