from user_scanner.core.orchestrator import generic_validate, Result


def validate_freesound(user):
    url = f"https://freesound.org/people/{user}/section/stats/?ajax=1"
    show_url = f"https://freesound.org/people/{user}/"

    def process(response):
        if response.status_code == 200 and "forum posts" in response.text.lower():
            extra = {}
            try:
                import re as local_re
                # 1. Sounds count
                sounds_match = local_re.search(r'([0-9]+)\s+sounds', response.text)
                if sounds_match:
                    extra["sounds"] = int(sounds_match.group(1))
                # 2. Packs count
                packs_match = local_re.search(r'([0-9]+)\s+packs', response.text)
                if packs_match:
                    extra["packs"] = int(packs_match.group(1))
                # 3. Audio duration minutes
                duration_match = local_re.search(r'([0-9:]+)\s+minutes', response.text)
                if duration_match:
                    extra["duration"] = duration_match.group(1)
                # 4. Average rating
                rating_match = local_re.search(r'([0-9.]+)\s+average rating', response.text)
                if rating_match:
                    extra["average_rating"] = float(rating_match.group(1))
                # 5. Downloads count
                downloads_match = local_re.search(r'([0-9]+)\s+downloads', response.text)
                if downloads_match:
                    extra["downloads"] = int(downloads_match.group(1))
                # 6. Forum posts
                forum_match = local_re.search(r'([0-9]+)\s+forum posts', response.text)
                if forum_match:
                    extra["forum_posts"] = int(forum_match.group(1))
            except Exception:
                pass
            return Result.taken(extra=extra)

        if response.status_code == 404 or "Page not found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

