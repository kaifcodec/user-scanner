from user_scanner.core.impersonate import impersonate_request, impersonate_validate
from user_scanner.core.result import Result


def validate_tindie(user: str) -> Result:
    signup_url = "https://www.tindie.com/accounts/signup/"

    def process(landing):
        if landing.status_code != 200:
            return Result.error(f"Unexpected signup status: {landing.status_code}")

        token = landing.cookies.get("csrftoken")
        if not token:
            return Result.error("CSRF token not found")

        response = impersonate_request(
            "https://www.tindie.com/accounts/check_username/",
            method="POST",
            data={"username": user},
            headers={
                "Referer": signup_url,
                "X-CSRFToken": token,
            },
        )

        if response.status_code == 429:
            return Result.error("Rate limited; try again later")
        if response.status_code != 200:
            return Result.error(f"Unexpected check status: {response.status_code}")

        match response.json():
            case {"valid": False, "errors": ["Username taken!"]}:
                extra, media = _seller_profile(user)
                return Result.taken(extra=extra, media=media)
            case {"valid": True, "errors": [], "message": "Username available!"}:
                return Result.available()
            case {"errors": [error, *_]}:
                return Result.error(str(error))
            case _:
                return Result.error("Unexpected username response")

    return impersonate_validate(signup_url, process, show_url="https://www.tindie.com/")


def _seller_profile(user: str) -> tuple[dict, dict]:
    try:
        response = impersonate_request(
            "https://www.tindie.com/api/v1/product/",
            params={"limit": 1, "store_username": user},
        )
        if response.status_code != 200:
            return {}, {}

        data = response.json()
        products = data.get("objects") or []
        store = products[0] if products else None
        if not isinstance(store, dict):
            return {}, {}
        if str(store.get("store_username", "")).casefold() != user.casefold():
            return {}, {}

        return (
            {
                "store_name": store.get("store_name"),
                "store_url": store.get("store_url"),
                "products": (data.get("meta") or {}).get("total_count"),
            },
            {"avatar": store.get("store_avatar")},
        )
    except Exception:
        return {}, {}
