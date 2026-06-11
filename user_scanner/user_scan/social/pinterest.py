from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_pinterest(user):
    url = f"https://www.pinterest.com/{user}/"
    show_url = f"https://www.pinterest.com/{user}/"

    def process(response):
        if response.status_code == 200:
            if "User not found." in response.text:
                return Result.available()
            
            extra = {}
            try:
                import re as local_re
                import json as local_json
                m = local_re.search(r'<script id="__PWS_INITIAL_PROPS__"[^>]*>(.*?)</script>', response.text)
                if m:
                    props_data = local_json.loads(m.group(1))
                    users_dict = props_data.get("initialReduxState", {}).get("users", {})
                    # Find user key that is a numeric ID (not empty string)
                    user_key = next((k for k in users_dict.keys() if k != ""), None)
                    if user_key and users_dict.get(user_key):
                        u_data = users_dict[user_key]
                        if u_data.get("full_name"):
                            extra["name"] = u_data.get("full_name")
                        if u_data.get("about"):
                            extra["bio"] = u_data.get("about").strip()
                        if u_data.get("follower_count") is not None:
                            extra["followers"] = u_data.get("follower_count")
                        if u_data.get("following_count") is not None:
                            extra["following"] = u_data.get("following_count")
                        if u_data.get("board_count") is not None:
                            extra["boards"] = u_data.get("board_count")
                        if u_data.get("pin_count") is not None:
                            extra["pins"] = u_data.get("pin_count")
                        if u_data.get("website_url"):
                            extra["website"] = u_data.get("website_url")
                        if u_data.get("image_xlarge_url"):
                            extra["avatar"] = u_data.get("image_xlarge_url")
                        elif u_data.get("image_medium_url"):
                            extra["avatar"] = u_data.get("image_medium_url")
            except Exception:
                pass
            
            return Result.taken(extra=extra)
        else:
            return Result.error("Invalid status code")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)

