from user_scanner.core.orchestrator import generic_validate, Result

def validate_freelancer(user):
    url = f"https://www.freelancer.com/api/users/0.1/users?usernames%5B%5D={user}&compact=true"
    show_url = f"https://www.freelancer.com/u/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                users = data.get('result', {}).get('users', {})
                if users:
                    u = list(users.values())[0]
                    extra = {}
                    if u.get('id'): extra['id'] = u.get('id')
                    if u.get('username'): extra['username'] = u.get('username')
                    if u.get('display_name'): extra['display_name'] = u.get('display_name')
                    if u.get('role'): extra['role'] = u.get('role')
                    if u.get('registration_date'): extra['registration_date'] = u.get('registration_date')
                    loc = u.get('location', {})
                    country = loc.get('country', {}).get('name')
                    city = loc.get('city')
                    if country and city: extra['location'] = f"{city}, {country}"
                    return Result.taken(extra=extra)
                else:
                    return Result.available()
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
