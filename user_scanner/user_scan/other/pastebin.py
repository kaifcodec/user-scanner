from user_scanner.core.orchestrator import generic_validate, Result
import re as local_re

def validate_pastebin(user):
    url = f"https://pastebin.com/u/{user}"
    show_url = url

    def process(response):
        if response.status_code == 200:
            if "info-bar" in response.text or "user-icon" in response.text:
                extra = {}
                html = response.text

                # Avatar
                avatar_match = local_re.search(r'<div class="user-icon">\s*<img src="([^"]+)"', html)
                if avatar_match:
                    avatar_src = avatar_match.group(1)
                    if "guest.png" not in avatar_src:
                        if avatar_src.startswith("/"):
                            avatar_src = "https://pastebin.com" + avatar_src
                        extra["avatar"] = avatar_src

                # Pro User
                if 'class="pro"' in html:
                    extra["pro_user"] = True

                # Views
                views_match = local_re.search(r'<span class="views"[^>]*>([\d,]+)</span>', html)
                if views_match:
                    extra["views"] = int(views_match.group(1).replace(",", ""))

                # All Views
                all_views_match = local_re.search(r'<span class="views -all"[^>]*>([\d,]+)</span>', html)
                if all_views_match:
                    extra["all_views"] = int(all_views_match.group(1).replace(",", ""))

                # Rating
                rating_match = local_re.search(r'<span class="rating"[^>]*>([^\s<]+)</span>', html)
                if rating_match:
                    extra["rating"] = rating_match.group(1)

                # Joined date
                joined_match = local_re.search(r'class="date-text"\s+title="([^"]+)"', html)
                if joined_match:
                    extra["joined"] = joined_match.group(1)

                # Website
                web_match = local_re.search(r'<a[^>]+class="web"[^>]*href="([^"]+)"', html)
                if web_match:
                    extra["website"] = web_match.group(1)

                # Location
                loc_match = local_re.search(r'<span[^>]+class="location"[^>]*>([\s\S]*?)</span>', html)
                if loc_match:
                    extra["location"] = loc_match.group(1).strip()

                return Result.taken(extra=extra)

            return Result.available()

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)

