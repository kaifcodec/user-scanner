from user_scanner.core.orchestrator import generic_validate, Result
import re as local_re
import json

def validate_zomato(user):
    url = f"https://www.zomato.com/{user}/reviews"
    show_url = url

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0"
    }

    def process(response):
        if response.status_code == 200:
            match = local_re.search(r'window\.__PRELOADED_STATE__\s*=\s*JSON\.parse\("([\s\S]*?)"\);', response.text)
            if not match:
                match = local_re.search(r'window\.__PRELOADED_STATE__\s*=\s*([\s\S]*?);', response.text)

            extra = {}
            if match:
                try:
                    raw_json_str = match.group(1)
                    if raw_json_str.startswith('"'):
                        decoded_js_str = json.loads(raw_json_str)
                    else:
                        decoded_js_str = json.loads(f'"{raw_json_str}"')
                    
                    data = json.loads(decoded_js_str)
                    user_id = data.get("pages", {}).get("current", {}).get("userId")
                    if user_id:
                        user_id_str = str(user_id)
                        basic_info = data.get("pages", {}).get("user", {}).get(user_id_str, {}).get("sections", {}).get("SECTION_USER_BASIC_INFO", {})
                        
                        if name := basic_info.get("name"):
                            extra["name"] = name.strip()
                        if bio := basic_info.get("bio"):
                            extra["bio"] = bio.strip()
                        if rank := basic_info.get("foodieRankText"):
                            extra["rank"] = rank.strip()
                        if country := basic_info.get("countryName"):
                            extra["country"] = country.strip()
                        if city := basic_info.get("cityName"):
                            extra["city"] = city.strip()
                        if followers := basic_info.get("followersCount"):
                            extra["followers"] = int(followers)
                        if reviews := basic_info.get("reviewsCount"):
                            extra["reviews"] = int(reviews)
                        if photos := basic_info.get("photoCount"):
                            extra["photos"] = int(photos)
                        if avatar := basic_info.get("profilePicture"):
                            extra["avatar"] = avatar.strip()
                        if website := basic_info.get("websiteLink"):
                            extra["website"] = website.strip()
                except Exception:
                    pass
            return Result.taken(extra=extra)

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)

