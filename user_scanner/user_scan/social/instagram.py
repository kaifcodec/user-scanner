import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_instagram(user: str) -> Result:
    if not (1 <= len(user) <= 30):
        return Result.error("Length must be between 1 and 30 characters")

    if not re.match(r"^[a-zA-Z0-9._-]+$", user):
        return Result.error(
            "Can only use letters, numbers, underscores, periods, or hyphens"
        )

    show_url = f"https://www.instagram.com/{user}/"
    api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "*/*",
        "x-ig-app-id": "936619743392459",
        "referer": show_url,
    }

    try:
        response = make_request(
            api_url, headers=headers, http2=True, timeout=10)

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                data = {}

            user_data = data.get("data", {}).get("user")
            if user_data:
                extra = {}

                # Base Fields
                if user_data.get("username"):
                    extra["username"] = user_data.get("username")
                if user_data.get("full_name"):
                    extra["fullname"] = user_data.get("full_name")
                if user_data.get("id"):
                    extra["id"] = user_data.get("id")
                if user_data.get("profile_pic_url_hd"):
                    extra["image"] = user_data.get("profile_pic_url_hd")
                if user_data.get("biography"):
                    extra["bio"] = user_data.get("biography")

                # Advanced/External Fields
                if user_data.get("business_email"):
                    extra["business_email"] = user_data.get("business_email")
                if user_data.get("external_url"):
                    extra["external_url"] = user_data.get("external_url")
                if user_data.get("fbid"):
                    extra["facebook_uid"] = user_data.get("fbid")

                # Boolean Flags
                if user_data.get("is_business_account") is not None:
                    extra["is_business"] = str(
                        user_data.get("is_business_account"))
                if user_data.get("is_joined_recently") is not None:
                    extra["is_joined_recently"] = str(
                        user_data.get("is_joined_recently"))
                if user_data.get("is_private") is not None:
                    extra["private"] = str(user_data.get("is_private"))
                if user_data.get("is_verified") is not None:
                    extra["verified"] = str(user_data.get("is_verified"))

                # Social Metrics
                if user_data.get("edge_followed_by", {}).get("count") is not None:
                    extra["follower_count"] = user_data.get(
                        "edge_followed_by", {}).get("count")
                if user_data.get("edge_follow", {}).get("count") is not None:
                    extra["following_count"] = user_data.get(
                        "edge_follow", {}).get("count")

                return Result.taken(extra=extra, url=show_url)
            else:
                # If API response succeeded but user object is empty/null, the user does not exist
                return Result.available(url=show_url)

        elif response.status_code == 404:
            return Result.available(url=show_url)

        elif response.status_code in (403, 429):
            signup_url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
            signup_headers = {
                "User-Agent": headers["User-Agent"],
                "Accept": "*/*",
                "x-ig-app-id": "936619743392459",
                "x-csrftoken": "0",
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
                "content-type": "application/x-www-form-urlencoded",
                "cookie": "csrftoken=0",
            }

            signup_data = {
                "username": user,
                "email": "",
                "first_name": "",
                "opt_into_one_tap": "false"
            }

            try:
                fallback_resp = make_request(
                    signup_url,
                    headers=signup_headers,
                    data=signup_data,
                    method="POST",
                    http2=True,
                    timeout=10
                )

                if fallback_resp.status_code == 200:
                    fb_data = fallback_resp.json()
                    errors = fb_data.get("errors", {})
                    username_errors = errors.get("username", [])

                    for err in username_errors:
                        if err.get("code") in ("username_invalid", "username_is_taken"):
                            return Result.taken(url=show_url)

                    return Result.available(url=show_url)
            except Exception:
                pass

            # If the fallback signup attempt also fails or gets blocked, notify the user gracefully
            return Result.error(
                f"Rate limit / Cloudflare protection block (HTTP {response.status_code}). Run with residential proxy or active session cookies.",
                url=show_url
            )

        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    except Exception as e:
        return Result.error(e, url=show_url)
