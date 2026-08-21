from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_paragraph(user):
    api_url = f"https://paragraph.com/api/blogs/@{user}"
    show_url = f"https://paragraph.com/@{user}"
    
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
                if "id" in data:
                    extra["id"] = data["id"]
                if "name" in data:
                    extra["name"] = data["name"]
                if "createdAt" in data:
                    extra["created_at"] = data["createdAt"]
                if "userId" in data:
                    extra["user_id"] = data["userId"]
                return Result.taken(extra=extra, url=show_url)
        except Exception:
            pass
    return Result.available(url=show_url)
