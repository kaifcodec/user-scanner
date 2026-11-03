from user_scanner.core.orchestrator import generic_validate, Result
from user_scanner.core.helpers import get_random_user_agent


def validate_cropty(user: str) -> Result:
    url = f"https://api.cropty.io/v1/auth/{user}"
    show_url = "https://www.cropty.io"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        try:
            data_json = response.json()
        except Exception:
            data_json = None

        if response.status_code == 200:
            if isinstance(data_json, dict) and "data" in data_json:
                data = data_json["data"]
                extra: dict[str, str] = {}
                media: dict[str, str] = {}
                if name := data.get("name"):
                    extra["name"] = name
                if nickname := data.get("nickname"):
                    extra["nickname"] = nickname
                if ref_code := data.get("ref_code"):
                    extra["referral_code"] = ref_code
                if ref_link := data.get("ref_link"):
                    extra["referral_link"] = ref_link
                if image := data.get("image"):
                    if "defaults" not in image:
                        media["avatar"] = image
                return Result.taken(extra=extra, media=media)
            return Result.error("Unexpected 200 response shape (no 'data')")

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)
