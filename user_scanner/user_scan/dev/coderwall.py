from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_coderwall(user):
    url = f"https://coderwall.com/{user}.json"
    show_url = f"https://coderwall.com/{user}"
    headers = {"User-Agent": get_random_user_agent(), "Accept": "application/json"}

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data and "username" in data:
                extra = {}
                if data.get("id"): extra["id"] = data.get("id")
                if data.get("name"): extra["name"] = data.get("name")
                if data.get("location"): extra["location"] = data.get("location")
                if data.get("karma") is not None: extra["karma"] = data.get("karma")
                if data.get("company"): extra["company"] = data.get("company")
                if data.get("about"): extra["about"] = data.get("about").strip()
                if data.get("thumbnail"): extra["avatar"] = data.get("thumbnail")
                
                accounts = data.get("accounts", {})
                if accounts:
                    for platform, handle in accounts.items():
                        if handle:
                            extra[f"{platform}_handle"] = handle
                            
                return Result.taken(extra=extra, url=show_url)
            return Result.available(url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
