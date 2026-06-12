from user_scanner.core.orchestrator import generic_validate, Result

def validate_500px(user):
    # Notice we pass the variables in URL encoded form, matching the query we inspected
    url = f"https://api.500px.com/graphql?query=query%28%24username%3AString%21%29%7BuserByUsername%28username%3A%24username%29%7Bid%20legacyId%20username%20displayName%20firstName%20lastName%20registeredAt%20userProfile%7Bfirstname%20lastname%20about%20country%20city%20state%7DsocialMedia%7Bwebsite%20twitter%20facebook%20instagram%7D%7D%7D&variables=%7B%22username%22%3A%22{user}%22%7D"
    show_url = f"https://500px.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json().get('data', {})
                user_data = data.get('userByUsername')
                if user_data:
                    extra = {}
                    if user_data.get('legacyId'):
                        extra['id'] = user_data.get('legacyId')
                    if user_data.get('displayName'):
                        extra['displayName'] = user_data.get('displayName')
                    if user_data.get('registeredAt'):
                        extra['registeredAt'] = user_data.get('registeredAt')
                    
                    profile = user_data.get('userProfile', {})
                    if profile.get('country'):
                        extra['country'] = profile.get('country')
                    if profile.get('city'):
                        extra['city'] = profile.get('city')
                    if profile.get('about'):
                        extra['about'] = profile.get('about')
                        
                    social = user_data.get('socialMedia', {})
                    for net in ['website', 'twitter', 'facebook', 'instagram']:
                        if social.get(net):
                            extra[net] = social.get(net)

                    return Result.taken(extra=extra)
                else:
                    return Result.available()
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
