import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_hex_pm(user: str) -> Result:
    """Validate a package author on Hex.pm (hex.pm)."""
    url = f"https://hex.pm/api/users/{user}"
    show_url = f"https://hex.pm/users/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    def process(response):
        # 1. Explicit verification of available / not-found state
        if response.status_code == 404 or "page not found" in response.text.lower():
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + Hex.pm user payload
        if response.status_code == 200 and '"username":' in response.text:
            try:
                data = json.loads(response.text)
                if (data.get("username") or "").lower() == user.lower():
                    extra = {}
                    media = {}

                    if username := data.get("username"):
                        extra["username"] = str(username).strip()
                    if full_name := data.get("full_name"):
                        extra["name"] = str(full_name).strip()
                    if email := data.get("email"):
                        extra["email"] = str(email).strip()
                    if inserted_at := data.get("inserted_at"):
                        extra["joined"] = str(inserted_at).strip()

                    handles = data.get("handles", {})
                    if github := handles.get("github"):
                        extra["github"] = str(github).strip()
                    if twitter := handles.get("twitter"):
                        extra["twitter"] = str(twitter).strip()

                    return Result.taken(extra=extra, media=media, url=show_url)
            except Exception:
                return Result.error("Failed to parse Hex.pm JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
