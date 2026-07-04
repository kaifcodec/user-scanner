from user_scanner.core.orchestrator import generic_validate, Result


def validate_lastfm(user):
    url = f"https://www.last.fm/user/{user}"
    show_url = f"https://www.last.fm/user/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                import re as local_re
                # 1. Display Name
                display_name_match = local_re.search(r'class="header-title-display-name">\s*([^<\n\r]+)', response.text)
                if display_name_match:
                    extra["display_name"] = display_name_match.group(1).strip()
                # 2. Scrobbling since
                since_match = local_re.search(r'scrobbling since\s*([^<\n\r]+)', response.text)
                if since_match:
                    extra["scrobbling_since"] = since_match.group(1).strip()
                # 3. Scrobbles
                scrobbles_match = local_re.search(r'Scrobbles.*?<p[^>]*>.*?<a[^>]*>([^<]+)</a>', response.text, local_re.DOTALL)
                if scrobbles_match:
                    extra["scrobbles"] = scrobbles_match.group(1).strip()
                # 4. Artists
                artists_match = local_re.search(r'Artists.*?<p[^>]*>.*?<a[^>]*>([^<]+)</a>', response.text, local_re.DOTALL)
                if artists_match:
                    extra["artists"] = artists_match.group(1).strip()
                # 5. Avatar
                avatar_match = local_re.search(r'src="([^"]+)"[^>]*alt="Avatar for [^"]+"[^>]*itemprop="image"', response.text, local_re.DOTALL)
                if avatar_match:
                    extra["avatar"] = avatar_match.group(1).strip()
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"HTTP {response.status_code}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    return generic_validate(url, process, show_url=show_url, headers=headers)

