import json
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_yandexmusic(user: str) -> Result:
    url = f"https://music.yandex.ru/users/{user}"
    api_url = f"https://music.yandex.ru/handlers/library.jsx?owner={user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Referer": f"{url}/playlists",
        "Accept": "application/json",
    }
    
    try:
        response = make_request(api_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                return Result.error("Failed to parse JSON response", url=url)
                
            owner = data.get("owner", {})
            if not owner or not owner.get("uid"):
                return Result.available(url=url)
                
            extra = {}
            if yuid := owner.get("uid"): extra["yandex_uid"] = str(yuid)
            if name := owner.get("name"): extra["fullname"] = name
            if verified := data.get("verified"): extra["is_verified"] = str(verified)
            
            counts = data.get("counts", {})
            if liked_albums := counts.get("likedAlbums"): extra["liked_albums"] = str(liked_albums)
            if liked_artists := counts.get("likedArtists"): extra["liked_artists"] = str(liked_artists)
            
            if has_tracks := data.get("hasTracks"): extra["has_tracks"] = str(has_tracks)
            
            return Result.taken(extra=extra, url=url)
            
        elif response.status_code == 404:
            return Result.available(url=url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=url)
            
    except Exception as e:
        return Result.error(e, url=url)
