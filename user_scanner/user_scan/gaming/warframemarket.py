from user_scanner.core.orchestrator import generic_validate, Result

def validate_warframemarket(user):
    url = f"https://api.warframe.market/v2/user/{user}"
    show_url = f"https://warframe.market/profile/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                res_data = response.json()
                data = res_data.get('data', {})
                if data and data.get('id'):
                    extra = {}
                    if data.get('id'):
                        extra['id'] = data.get('id')
                    if data.get('role'):
                        extra['role'] = data.get('role')
                    if data.get('ingameName'):
                        extra['ingameName'] = data.get('ingameName')
                    if data.get('reputation') is not None:
                        extra['reputation'] = data.get('reputation')
                    if data.get('masteryRank') is not None:
                        extra['masteryRank'] = data.get('masteryRank')
                    if data.get('status'):
                        extra['status'] = data.get('status')
                    if data.get('lastSeen'):
                        extra['lastSeen'] = data.get('lastSeen')
                    if data.get('platform'):
                        extra['platform'] = data.get('platform')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
