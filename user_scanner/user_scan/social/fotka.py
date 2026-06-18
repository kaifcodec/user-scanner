from user_scanner.core.orchestrator import generic_validate, Result

def validate_fotka(user):
    url = f"https://api.fotka.com/v2/user/dataStatic?login={user}"
    show_url = f"https://fotka.com/profil/{user}"

    def process(response):
        if response.status_code == 404 or '"status":"ERROR"' in response.text:
            return Result.available()

        if response.status_code == 200:
            try:
                data = response.json()
                profil = data.get('profil', {})
                if profil and profil.get('id'):
                    extra = {}
                    if profil.get('id'):
                        extra['id'] = profil.get('id')
                    if profil.get('sex'):
                        extra['sex'] = profil.get('sex')
                    if profil.get('age'):
                        extra['age'] = profil.get('age')
                    if profil.get('city'):
                        extra['city'] = profil.get('city')
                    if profil.get('creationTS'):
                        extra['creationTS'] = profil.get('creationTS')
                    if profil.get('photosNumber') is not None:
                        extra['photosNumber'] = profil.get('photosNumber')

                    return Result.taken(extra=extra)
            except Exception:
                pass

            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
