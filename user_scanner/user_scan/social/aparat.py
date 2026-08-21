import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_aparat(user: str) -> Result:
    """Validate a username on Aparat (aparat.com)."""
    url = f"https://www.aparat.com/api/fa/v1/user/user/information/username/{user}"
    show_url = f"https://www.aparat.com/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        # 1. Explicit check for not-found state (HTTP 404 or explicit error detail)
        if response.status_code == 404 or "page not found" in response.text.lower():
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + deep data extraction
        if response.status_code == 200 and "attributes" in response.text:
            try:
                data = json.loads(response.text)
                attrs = data.get("data", {}).get("attributes", {})
                username = attrs.get("username")

                if username and str(username).lower() == user.lower():
                    extra = {}
                    media = {}

                    if name := attrs.get("name"):
                        extra["name"] = str(name).strip()
                    if descr := attrs.get("descr"):
                        if str(descr).strip():
                            extra["bio"] = str(descr).strip()
                    if followers := (attrs.get("follower_cnt_num") or attrs.get("follower_cnt")):
                        extra["followers"] = str(followers)
                    if following := attrs.get("follow_cnt"):
                        extra["following"] = str(following)
                    if video_cnt := attrs.get("video_cnt"):
                        extra["videos"] = str(video_cnt)
                    if website := attrs.get("url"):
                        if str(website).strip() and str(website).strip() != "http://www.aparat.com":
                            extra["website"] = str(website).strip()

                    avatar = attrs.get("pic_b") or attrs.get("pic_m") or attrs.get("pic_s")
                    if avatar and str(avatar).strip():
                        media["avatar"] = str(avatar).strip()

                    return Result.taken(extra=extra, media=media, url=show_url)
            except Exception:
                return Result.error("Failed to parse Aparat JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes or unhandled responses (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
