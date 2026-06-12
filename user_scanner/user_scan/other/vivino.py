from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_vivino(user):
    api_url = f"https://api.vivino.com/users/{user}"
    show_url = f"https://www.vivino.com/users/{user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }
    
    resp = make_request(api_url, headers=headers, http2=True)
    if resp.status_code == 200:
        try:
            data = resp.json()
            if "id" in data:
                extra = {}
                extra["id"] = data["id"]
                if "alias" in data:
                    extra["alias"] = data["alias"]
                if "seo_name" in data:
                    extra["seo_name"] = data["seo_name"]
                if "is_premium" in data:
                    extra["is_premium"] = data["is_premium"]
                if "image" in data and data["image"] and "location" in data["image"]:
                    img = data["image"]["location"]
                    if img.startswith("//"):
                        img = "https:" + img
                    extra["image"] = img
                if "language" in data:
                    extra["language"] = data["language"]
                return Result.taken(extra=extra, url=show_url)
        except Exception:
            pass
    return Result.available(url=show_url)
