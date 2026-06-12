from user_scanner.core.orchestrator import generic_validate, Result

def validate_statsfm(user):
    url = f"https://api.stats.fm/api/v1/users/{user}"
    show_url = f"https://stats.fm/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                item = data.get('item', {})
                if item and item.get('id'):
                    extra = {}
                    if item.get('id'):
                        extra['id'] = item.get('id')
                    if item.get('displayName'):
                        extra['displayName'] = item.get('displayName')
                    if item.get('createdAt'):
                        extra['createdAt'] = item.get('createdAt')
                    if item.get('isPlus') is not None:
                        extra['isPlus'] = item.get('isPlus')
                    if item.get('isPro') is not None:
                        extra['isPro'] = item.get('isPro')
                    if item.get('quarantined') is not None:
                        extra['quarantined'] = item.get('quarantined')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
