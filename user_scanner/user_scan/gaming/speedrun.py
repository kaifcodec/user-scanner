from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_speedrun(user):
    url = f"https://www.speedrun.com/api/v1/users/{user}"
    show_url = f"https://www.speedrun.com/users/{user}"
    headers = {"User-Agent": get_random_user_agent(), "Accept": "application/json"}

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.json().get("data", {})
            if data:
                extra = {}
                if data.get("id"): extra["id"] = data.get("id")
                
                names = data.get("names", {})
                if names.get("international"):
                    extra["name"] = names.get("international")
                    
                if data.get("role"): extra["role"] = data.get("role")
                if data.get("signup"): extra["signup"] = data.get("signup")
                
                location = data.get("location", {})
                if location:
                    country_info = location.get("country", {})
                    region_info = location.get("region", {})
                    country = country_info.get("names", {}).get("international") if country_info else None
                    region = region_info.get("names", {}).get("international") if region_info else None
                    if country and region:
                        extra["location"] = f"{region}, {country}"
                    elif country:
                        extra["location"] = country
                
                for platform in ["twitch", "youtube", "twitter"]:
                    plat_info = data.get(platform)
                    if plat_info and plat_info.get("uri"):
                        extra[platform] = plat_info.get("uri")
                        
                return Result.taken(extra=extra, url=show_url)
            return Result.available(url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
