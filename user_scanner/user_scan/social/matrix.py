import urllib.parse
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_matrix(user: str) -> Result:
    # Support username or full MXID @user:server
    if ":" in user:
        mxid = user if user.startswith("@") else f"@{user}"
    else:
        mxid = f"@{user}:matrix.org"

    encoded_mxid = urllib.parse.quote(mxid)
    url = f"https://matrix.org/_matrix/client/v3/profile/{encoded_mxid}"
    show_url = f"https://matrix.to/#/{encoded_mxid}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
    }

    def process(response) -> Result:
        if response.status_code == 200:
            try:
                data = response.json()
                extra: dict[str, str] = {}
                media: dict[str, str] = {}

                displayname = data.get("displayname")
                if displayname:
                    extra["name"] = str(displayname)

                avatar_url = data.get("avatar_url")
                if avatar_url:
                    extra["mxc_avatar"] = str(avatar_url)
                    # Convert mxc:// URI to matrix.org media repo URL
                    if avatar_url.startswith("mxc://"):
                        mxc_path = avatar_url[6:]
                        media["avatar"] = f"https://matrix.org/_matrix/media/v3/download/{mxc_path}"

                return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                return Result.taken(url=show_url)

        if response.status_code == 404:
            return Result.available()

        if response.status_code == 400:
            return Result.available()

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
