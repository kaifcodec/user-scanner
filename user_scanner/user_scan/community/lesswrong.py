import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_lesswrong(user: str) -> Result:
    """Validate a user profile on LessWrong (lesswrong.com)."""
    url = "https://www.lesswrong.com/graphql"
    show_url = f"https://www.lesswrong.com/users/{user}"

    query = (
        '{ user(input: {selector: {slug: "'
        + user
        + '"}}) { result { _id displayName slug karma bio createdAt } } }'
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def process(response):
        # 1. Explicit verification of available / not-found state
        if (
            response.status_code == 404
            or "app.missing_document" in response.text
            or '"user":null' in response.text.replace(" ", "")
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and '"user":' in response.text:
            try:
                data = json.loads(response.text)
                user_res = data.get("data", {}).get("user", {}).get("result")
                if user_res:
                    extra = {}
                    media = {}

                    if display_name := user_res.get("displayName"):
                        extra["name"] = str(display_name).strip()
                    if slug := user_res.get("slug"):
                        extra["username"] = str(slug).strip()
                    if user_id := user_res.get("_id"):
                        extra["user_id"] = str(user_id).strip()
                    if karma := user_res.get("karma"):
                        extra["karma"] = str(karma)
                    if created_at := user_res.get("createdAt"):
                        extra["created_at"] = str(created_at).strip()
                    if bio := user_res.get("bio"):
                        clean_bio = str(bio).strip()
                        if clean_bio:
                            extra["bio"] = clean_bio

                    return Result.taken(extra=extra, media=media, url=show_url)
            except Exception:
                return Result.error("Failed to parse LessWrong GraphQL response", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(
        url,
        process,
        method="POST",
        json={"query": query},
        headers=headers,
        show_url=show_url,
    )
