from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_bluesky(user):
    handle = user if user.endswith(".bsky.social") else f"{user}.bsky.social"
    url = "https://bsky.social/xrpc/com.atproto.temp.checkHandleAvailability"
    show_url = f"https://bsky.app/profile/{user}.bsky.social"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Encoding": "gzip",
        "atproto-accept-labelers": "did:plc:ar7c4by46qjdydhdevvrndac;redact",
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?1",
        "origin": "https://bsky.app",
        "sec-fetch-site": "cross-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://bsky.app/",
        "accept-language": "en-US,en;q=0.9",
    }

    params = {
        "handle": handle,
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            result_type = data.get("result", {}).get("$type")

            if (
                result_type
                == "com.atproto.temp.checkHandleAvailability#resultAvailable"
            ):
                return Result.available()
            elif (
                result_type
                == "com.atproto.temp.checkHandleAvailability#resultUnavailable"
            ):
                extra = {}
                try:
                    import httpx
                    profile_res = httpx.get(
                        "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile",
                        params={"actor": handle},
                        headers={"User-Agent": headers["User-Agent"]},
                        timeout=5.0
                    )
                    if profile_res.status_code == 200:
                        p_data = profile_res.json()
                        if p_data.get("displayName"):
                            extra["display_name"] = p_data.get("displayName")
                        if p_data.get("description"):
                            extra["bio"] = p_data.get("description").strip()
                        if p_data.get("followersCount") is not None:
                            extra["followers"] = p_data.get("followersCount")
                        if p_data.get("followsCount") is not None:
                            extra["following"] = p_data.get("followsCount")
                        if p_data.get("postsCount") is not None:
                            extra["posts"] = p_data.get("postsCount")
                        if p_data.get("avatar"):
                            extra["avatar"] = p_data.get("avatar")
                except Exception:
                    pass
                return Result.taken(extra=extra)
        elif response.status_code == 400:
            return Result.error(
                "Username can only contain letters, numbers, hyphens (no leading/trailing)"
            )

        return Result.error("Invalid status code!")

    return generic_validate(
        url, process, show_url=show_url, headers=headers, params=params, timeout=15.0
    )
