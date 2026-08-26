import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_civitai(user: str) -> Result:
    """Validate a creator on Civitai (civitai.com)."""
    url = "https://civitai.com/api/v1/creators"
    show_url = f"https://civitai.com/user/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + Civitai creators JSON response
        if response.status_code == 200 and "items" in response.text:
            try:
                data = json.loads(response.text)
                items = data.get("items", [])

                if not items or len(items) == 0:
                    return Result.available(url=show_url)

                matched_creator = None
                for item in items:
                    if (item.get("username") or "").lower() == user.lower():
                        matched_creator = item
                        break

                if not matched_creator and items:
                    matched_creator = items[0]

                if matched_creator:
                    extra = {}
                    media = {}

                    if creator_name := matched_creator.get("username"):
                        extra["username"] = str(creator_name).strip()
                    if model_count := matched_creator.get("modelCount"):
                        extra["models_count"] = str(model_count)
                    if creator_link := matched_creator.get("link"):
                        extra["models_api"] = str(creator_link).strip()

                    if avatar := matched_creator.get("image"):
                        media["avatar"] = str(avatar).strip()

                    return Result.taken(extra=extra, media=media, url=show_url)

                return Result.available(url=show_url)
            except Exception:
                return Result.error("Failed to parse Civitai JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(
        url, process, headers=headers, show_url=show_url,
        follow_redirects=True, params={"query": user},
    )
