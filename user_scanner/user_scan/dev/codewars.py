from user_scanner.core.orchestrator import generic_validate, Result

def validate_codewars(user):
    url = f"https://www.codewars.com/api/v1/users/{user}"
    show_url = f"https://www.codewars.com/users/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get('id'):
                    extra = {}
                    if data.get('id'): extra['id'] = data.get('id')
                    if data.get('name'): extra['name'] = data.get('name')
                    if data.get('honor') is not None: extra['honor'] = data.get('honor')
                    if data.get('clan'): extra['clan'] = data.get('clan')
                    if data.get('leaderboardPosition') is not None: extra['leaderboard_position'] = data.get('leaderboardPosition')
                    ranks = data.get('ranks', {}).get('overall', {})
                    if ranks.get('name'): extra['rank_name'] = ranks.get('name')
                    if ranks.get('score') is not None: extra['score'] = ranks.get('score')
                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
