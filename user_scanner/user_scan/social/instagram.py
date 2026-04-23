import httpx

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_instagram(user):
    show_url = f"https://www.instagram.com/{user}/"
    url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "*/*",
        "x-ig-app-id": "936619743392459",
        "x-csrftoken": "0",
        "x-requested-with": "XMLHttpRequest",
        "referer": "https://www.instagram.com/accounts/emailsignup/",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": "csrftoken=0",
    }

    def check_response(response: httpx.Response) -> Result:
        try:
            data = response.json()
        except Exception:
            return Result.error(f"[{response.status_code}] Unexpected response from Instagram.")

        errors = data.get("errors", {})
        username_errors = errors.get("username", [])

        for err in username_errors:
            if err.get("code") in ("username_invalid", "username_is_taken"):
                return Result.taken()

        return Result.available()

    return generic_validate(
        url,
        check_response,
        show_url=show_url,
        headers=headers,
        data={"username": user, "email": "", "first_name": "", "opt_into_one_tap": "false"},
        method="POST",
        http2=True,
    )
