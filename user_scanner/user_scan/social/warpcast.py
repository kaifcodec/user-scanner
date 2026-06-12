from user_scanner.core.orchestrator import generic_validate, Result

def validate_warpcast(user):
    url = f"https://client.warpcast.com/v2/user-by-username?username={user}"
    show_url = f"https://warpcast.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                result = data.get('result', {}).get('user', {})
                if result:
                    extra = {}
                    if result.get('fid'): extra['fid'] = result.get('fid')
                    if result.get('displayName'): extra['displayname'] = result.get('displayName')
                    profile = result.get('profile', {})
                    bio = profile.get('bio', {})
                    if bio.get('text'): extra['bio'] = bio.get('text')
                    loc = profile.get('location', {})
                    if loc.get('description'): extra['location'] = loc.get('description')
                    if result.get('accountLevel'): extra['accountLevel'] = result.get('accountLevel')
                    if result.get('followerCount'): extra['followers'] = result.get('followerCount')
                    if result.get('followingCount'): extra['following'] = result.get('followingCount')
                    
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code in [400, 404]:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
