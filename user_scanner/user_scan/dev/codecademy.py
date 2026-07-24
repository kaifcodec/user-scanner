from user_scanner.core.orchestrator import generic_validate, Result
import json
import re

def validate_codecademy(user):
    url = f"https://www.codecademy.com/profiles/{user}"

    def process(response):
        location = response.headers.get("Location", "")
        if response.status_code in [301, 302, 303, 307, 308] or "login" in location:
            return Result.taken(extra={"is_private": True})
            
        elif response.status_code == 404:
            return Result.available()
            
        elif response.status_code == 200:
            try:
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
                if match:
                    data = json.loads(match.group(1))
                    user_data = data.get("props", {}).get("pageProps", {}).get("profile", {})
                    if user_data and user_data.get("username"):
                        extra = {"is_private": False}
                        if user_data.get("name"):
                            extra["name"] = user_data.get("name")
                        if user_data.get("bio"):
                            extra["bio"] = user_data.get("bio")
                        if user_data.get("location"):
                            extra["location"] = user_data.get("location")
                        if user_data.get("createdAt"):
                            extra["joined"] = user_data.get("createdAt")
                        return Result.taken(extra=extra)
                    else:
                        return Result.available()
                    
                if f"profiles/{user}" in response.text or user in response.text:
                    return Result.taken(extra={"is_private": False})
                return Result.available()
            except Exception:
                return Result.error("200 response status with no recognizable data, report it via GitHub issues")

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    return generic_validate(url, process, show_url=url, headers=headers, follow_redirects=False)
