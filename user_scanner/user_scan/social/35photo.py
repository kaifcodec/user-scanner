from user_scanner.core.orchestrator import generic_validate, Result

def validate_35photo(user):
    url = f"https://35photo.pro/@{user}/"
    show_url = url

    def process(response):
        if '<span title="Total photos' in response.text:
            extra = {}
            try:
                import re as local_re
                # Name
                name_match = local_re.search(r'<h1 class="thinFont">([^<]+)</h1>', response.text)
                if name_match:
                    extra["name"] = name_match.group(1).strip()
                # Location
                loc_match = local_re.search(r'title="Photographers from ([^"]+)"', response.text)
                if loc_match:
                    extra["country"] = loc_match.group(1).strip()
                city_match = local_re.search(r'title="Photographers from the city of\s*([^"]+)"', response.text)
                if city_match:
                    extra["city"] = city_match.group(1).strip()
                # Total photos
                photos_match = local_re.search(r'Total photos see.*?font-size:2.6em">([0-9]+)</span>', response.text, local_re.DOTALL)
                if photos_match:
                    extra["photos"] = int(photos_match.group(1))
                # Avatar
                avatar_match = local_re.search(r'img class="avatar140"\s+src="([^"]+)"', response.text)
                if avatar_match:
                    extra["avatar"] = avatar_match.group(1)
            except Exception:
                pass
            return Result.taken(extra=extra)
        
        if "Catalogs of professional author" in response.text or response.status_code == 302:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

