from user_scanner.core.orchestrator import generic_validate, Result
from user_scanner.core.helpers import get_random_user_agent

def validate_cropty(user):
    url = f"https://api.cropty.io/v1/auth/{user}"
    show_url = "https://www.cropty.io"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json"
    }

    def process(response):
        if response.status_code == 200:
            try:
                data_json = response.json()
                if "data" in data_json:
                    data = data_json["data"]
                    extra = {}
                    if name := data.get("name"): extra["name"] = name
                    if nickname := data.get("nickname"): extra["nickname"] = nickname
                    if image := data.get("image"):
                        if "defaults" not in image:
                            extra["avatar"] = image
                    if ref_link := data.get("ref_link"): extra["referral_link"] = ref_link
                    return Result.taken(extra=extra)
            except Exception:
                pass
            return Result.taken()

        if response.status_code == 404:
            return Result.available()

        
        try:
            data_json = response.json()

            if (
                "errors" in data_json
                and data_json["errors"]
                and data_json["errors"][0].get("code") == "ModelNotFoundException"
            ):
                return Result.available()

        except Exception:
            pass
        
        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)
