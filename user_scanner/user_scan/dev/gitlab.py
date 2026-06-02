from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_gitlab(user):
    url = f"https://gitlab.com/api/v4/users?username={user}"
    show_url = f"https://gitlab.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                if len(data) == 0:
                    return Result.available()
                else:
                    import re
                    extra = {}
                    try:
                        u_data = data[0]
                        if u_data.get("id"):
                            extra["uid"] = str(u_data.get("id"))
                        if u_data.get("name"):
                            extra["fullname"] = u_data.get("name").strip()
                        if u_data.get("username"):
                            extra["username"] = u_data.get("username").strip()
                        if u_data.get("state"):
                            extra["state"] = u_data.get("state")
                        
                        avatar_url = u_data.get("avatar_url")
                        if avatar_url:
                            extra["image"] = avatar_url
                            # Extract gravatar fields
                            m = re.search(r'gravatar\.com/avatar/([a-f0-9]{32})', avatar_url)
                            if m:
                                md5_hash = m.group(1)
                                extra["gravatar_url"] = f"https://gravatar.com/{md5_hash}"
                                extra["gravatar_username"] = u_data.get("username", "")
                                extra["gravatar_email_md5_hash"] = md5_hash
                    except Exception:
                        pass
                    return Result.taken(extra=extra)
        return Result.error(f"Unexpected status or response: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)

