from user_scanner.core.orchestrator import generic_validate, Result

def validate_omglol(user):
    url = f"https://api.omg.lol/address/{user}/info"
    show_url = f"https://omg.lol/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                r = data.get('response', {})
                if r and r.get('address'):
                    extra = {}
                    if r.get('address'): extra['address'] = r.get('address')
                    if r.get('message'): extra['message'] = r.get('message')
                    reg = r.get('registration', {})
                    if reg.get('date'): extra['registration_date'] = reg.get('date')
                    if reg.get('expiration'): extra['expiration'] = reg.get('expiration')
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
