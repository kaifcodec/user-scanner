from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request
import re, json


def validate_youtube(user) -> Result:
    url = f"https://www.youtube.com/@{user}"
    show_url = f"https://youtube.com/@{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            if "This channel does not exist" in response.text or "404 Not Found" in response.text:
                return Result.available(url=show_url)
            
            extra = {}
            m = re.search(r'var ytInitialData = (\{.*?\});', response.text)
            if m:
                try:
                    data = json.loads(m.group(1))
                    meta = data.get('metadata', {}).get('channelMetadataRenderer', {})
                    if title := meta.get('title'): extra['fullname'] = title
                    if desc := meta.get('description'): extra['bio'] = desc
                    if cid := meta.get('externalId'): extra['youtube_channel_id'] = cid
                    if purl := meta.get('vanityChannelUrl'): extra['channel_url'] = purl
                    if safe := meta.get('isFamilySafe'): extra['is_family_safe'] = str(safe)
                    if kw := meta.get('keywords'): extra['keywords'] = kw
                    if thumbs := meta.get('avatar', {}).get('thumbnails'):
                        if len(thumbs) > 0: extra['image'] = thumbs[0].get('url')
                except Exception:
                    pass
                    
            subs = re.search(r'\"content\":\"([0-9.]+[A-Z]? subscribers)\"', response.text)
            if subs: extra['subscribers'] = subs.group(1)
            
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
