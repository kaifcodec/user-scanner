from user_scanner.core.orchestrator import generic_validate, Result

def validate_sportstracker(user):
    url = f"https://api.sports-tracker.com/apiserver/v1/user/name/{user}"
    show_url = f"https://www.sports-tracker.com/view_profile/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                payload = data.get('payload', {})
                if payload and payload.get('username'):
                    extra = {}
                    if payload.get('uuid'):
                        extra['uuid'] = payload.get('uuid')
                    if payload.get('realName'):
                        extra['realName'] = payload.get('realName')
                    if payload.get('country'):
                        extra['country'] = payload.get('country')
                    if payload.get('city'):
                        extra['city'] = payload.get('city')
                    if payload.get('gender'):
                        extra['gender'] = payload.get('gender')
                    if payload.get('createdDate'):
                        extra['createdDate'] = payload.get('createdDate')
                    if payload.get('followersCount') is not None:
                        extra['followers'] = payload.get('followersCount')
                    if payload.get('followingCount') is not None:
                        extra['following'] = payload.get('followingCount')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404 or "Not Found" in response.text:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
