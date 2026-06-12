from user_scanner.core.orchestrator import generic_validate, Result

def validate_codeforces(user):
    url = f"https://codeforces.com/api/user.info?handles={user}"
    show_url = f"https://codeforces.com/profile/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('status') == 'OK' and data.get('result'):
                    res = data['result'][0]
                    extra = {}
                    if res.get('firstName'):
                        extra['firstName'] = res.get('firstName')
                    if res.get('lastName'):
                        extra['lastName'] = res.get('lastName')
                    if res.get('country'):
                        extra['country'] = res.get('country')
                    if res.get('city'):
                        extra['city'] = res.get('city')
                    if res.get('organization'):
                        extra['organization'] = res.get('organization')
                    if res.get('rating') is not None:
                        extra['rating'] = res.get('rating')
                    if res.get('maxRating') is not None:
                        extra['maxRating'] = res.get('maxRating')
                    if res.get('rank'):
                        extra['rank'] = res.get('rank')
                    if res.get('maxRank'):
                        extra['maxRank'] = res.get('maxRank')
                    if res.get('friendOfCount') is not None:
                        extra['friendOfCount'] = res.get('friendOfCount')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 400 or response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
