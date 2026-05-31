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

    return generic_validate(url, process, show_url=show_url)

