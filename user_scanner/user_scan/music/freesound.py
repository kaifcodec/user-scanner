from user_scanner.core.orchestrator import generic_validate, Result, make_request
import re

def validate_freesound(user):
    main_url = f"https://freesound.org/people/{user}/"
    show_url = main_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 403:
            return Result.error("Freesound rate limit or blocked with status code 403")

        if response.status_code == 404 or "Page not found" in response.text:
            return Result.available()

        final_url = str(response.url)
        match = re.search(r'/people/([^/]+)', final_url)
        if not match:
            return Result.available()
        canonical_user = match.group(1)

        stats_url = f"https://freesound.org/people/{canonical_user}/section/stats/?ajax=1"
        try:
            stats_resp = make_request(stats_url, headers=headers)
            if stats_resp.status_code == 200:
                extra = {}
                text = stats_resp.text
                
                sounds_match = re.search(r'title="[^"]*uploaded\s+([0-9,]+)\s+sounds?"', text)
                if sounds_match:
                    extra["sounds"] = int(sounds_match.group(1).replace(",", ""))
                    
                packs_match = re.search(r'title="[^"]*created\s+([0-9,]+)\s+packs?"', text)
                if packs_match:
                    extra["packs"] = int(packs_match.group(1).replace(",", ""))
                    
                duration_match = re.search(r'title="[^"]*together account for\s+([^\s"]+\s+(?:hours|minutes|seconds|hour|minute|second))\s+of', text)
                if duration_match:
                    extra["duration"] = duration_match.group(1).strip()
                    
                rating_match = re.search(r'title="[^"]*average rating of\s+([0-9.]+)"', text)
                if rating_match:
                    extra["average_rating"] = float(rating_match.group(1))
                    
                downloads_match = re.search(r'title="[^"]*downloaded\s+([0-9,]+)\s+times"', text)
                if downloads_match:
                    extra["downloads"] = int(downloads_match.group(1).replace(",", ""))
                    
                forum_match = re.search(r'title="[^"]*written\s+([0-9,]+)\s+forum"', text)
                if forum_match:
                    extra["forum_posts"] = int(forum_match.group(1).replace(",", ""))
                    
                return Result.taken(extra=extra)
        except Exception:
            pass

        return Result.taken()

    return generic_validate(main_url, process, show_url=show_url, headers=headers, follow_redirects=True)
