from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_soundcloud(user):
    url = f"https://soundcloud.com/{user}"
    show_url = f"https://soundcloud.com/{user}"

    def process(response):
        if response.status_code == 403:
            return Result.error("[403] Request forbidden try using proxy or VPN")

        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200:
            text = response.text

            is_taken = False
            if f"soundcloud://users:{user}" in text:
                is_taken = True
            elif f'"username":"{user}"' in text:
                is_taken = True
            elif "soundcloud://users:" in text and '"username":"' in text:
                is_taken = True

            if is_taken:
                extra = {}
                try:
                    import re as local_re
                    import json as local_json
                    m = local_re.search(r'window\.__sc_hydration\s*=\s*(.*?);', text)
                    if m:
                        hydration_data = local_json.loads(m.group(1))
                        user_item = next((item for item in hydration_data if item.get("hydratable") == "user"), None)
                        if user_item and user_item.get("data"):
                            u_data = user_item["data"]
                            if u_data.get("id"):
                                extra["id"] = u_data.get("id")
                            if u_data.get("full_name"):
                                extra["name"] = u_data.get("full_name").strip()
                            if u_data.get("city") or u_data.get("country_code"):
                                locs = [u_data.get("city"), u_data.get("country_code")]
                                extra["location"] = ", ".join(filter(None, locs))
                            if u_data.get("description"):
                                extra["bio"] = u_data.get("description").strip()
                            if u_data.get("followers_count") is not None:
                                extra["followers"] = u_data.get("followers_count")
                            if u_data.get("followings_count") is not None:
                                extra["following"] = u_data.get("followings_count")
                            if u_data.get("track_count") is not None:
                                extra["tracks"] = u_data.get("track_count")
                            if u_data.get("playlist_count") is not None:
                                extra["playlists"] = u_data.get("playlist_count")
                            if u_data.get("likes_count") is not None:
                                extra["likes"] = u_data.get("likes_count")
                            if u_data.get("avatar_url"):
                                extra["avatar"] = u_data.get("avatar_url")
                            if u_data.get("verified"):
                                extra["verified"] = "Yes"
                except Exception:
                    pass
                return Result.taken(extra=extra)

            return Result.error("Unexpected response, report it via GitHub issues")

        return Result.error("Unknown Error report it via GitHub issues")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
