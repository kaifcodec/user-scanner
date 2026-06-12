from user_scanner.core.orchestrator import generic_validate, Result

def validate_vimeo(user):
    url = f"https://vimeo.com/api/v2/{user}/info.json"
    show_url = f"https://vimeo.com/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get('id'):
                    extra = {}
                    if data.get('id'):
                        extra['id'] = data.get('id')
                    if data.get('display_name'):
                        extra['display_name'] = data.get('display_name')
                    if data.get('created_on'):
                        extra['created_on'] = data.get('created_on')
                    if data.get('location'):
                        extra['location'] = data.get('location')
                    if data.get('bio'):
                        extra['bio'] = data.get('bio')
                    if data.get('total_videos_uploaded') is not None:
                        extra['videos'] = data.get('total_videos_uploaded')
                    if data.get('total_contacts') is not None:
                        extra['contacts'] = data.get('total_contacts')
                    if data.get('total_channels') is not None:
                        extra['channels'] = data.get('total_channels')
                    if data.get('total_videos_liked') is not None:
                        extra['liked'] = data.get('total_videos_liked')

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()
            
        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
