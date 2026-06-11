import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request
from urllib.parse import quote
import json


def validate_leetcode(user: str) -> Result:
    if not (3 <= len(user) <= 30):
        return Result.error("Length must be between 3 and 30 characters")

    if not re.match(r"^[a-zA-Z0-9._-]+$", user):
        return Result.error(
            "Can only use letters, numbers, underscores, periods, or hyphens"
        )

    show_url = f"https://leetcode.com/u/{user}/"
    
    query = '''query userPublicProfile($username: String!) { matchedUser(username: $username) { username profile { realName aboutMe userAvatar countryName company school ranking } } }'''
    variables = json.dumps({"username": user})
    url = f"https://leetcode.com/graphql?query={quote(query)}&variables={quote(variables)}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
    }

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("errors") and "That user does not exist" in str(data.get("errors")):
                return Result.available(url=show_url)
            
            matched_user = data.get("data", {}).get("matchedUser")
            if matched_user:
                extra = {}
                profile = matched_user.get("profile", {})
                
                if profile.get("realName"): extra["fullname"] = profile.get("realName")
                if profile.get("aboutMe"): extra["bio"] = profile.get("aboutMe")
                if profile.get("userAvatar"): extra["image"] = profile.get("userAvatar")
                if profile.get("countryName"): extra["country"] = profile.get("countryName")
                if profile.get("company"): extra["company"] = profile.get("company")
                if profile.get("school"): extra["school"] = profile.get("school")
                if profile.get("ranking"): extra["ranking"] = profile.get("ranking")
                
                return Result.taken(extra=extra, url=show_url)
                
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
