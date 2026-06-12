from user_scanner.core.orchestrator import generic_validate, Result

def validate_microsoftlearn(user):
    url = f"https://learn.microsoft.com/api/profiles/{user}"
    show_url = f"https://learn.microsoft.com/en-us/users/{user}/"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('userId'):
                    extra = {}
                    if data.get('displayName'):
                        extra['name'] = data.get('displayName')
                    if data.get('reputationPoints') is not None:
                        extra['reputation'] = data.get('reputationPoints')
                    if data.get('followerCount') is not None:
                        extra['followers'] = data.get('followerCount')
                    if data.get('followingCount') is not None:
                        extra['following'] = data.get('followingCount')
                    if data.get('answersAccepted') is not None:
                        extra['answers_accepted'] = data.get('answersAccepted')
                    if data.get('createdOn'):
                        extra['created_on'] = data.get('createdOn')
                        
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
