from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_openstreetmap(user):
    url = f"https://www.openstreetmap.org/user/{user}"
    show_url = f"https://www.openstreetmap.org/user/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if "Mapper since" in response.text:
            extra = {}
            try:
                import re as local_re
                match = local_re.search(r"Mapper since:</dt>\s*<dd[^>]*>([^<]+)</dd>", response.text)
                if match:
                    extra["joined"] = match.group(1).strip()
                avatar_match = local_re.search(r'class="user_image"[^>]*src="([^"]+)"', response.text)
                if avatar_match:
                    img_url = avatar_match.group(1)
                    if img_url.startswith("/"):
                        img_url = "https://www.openstreetmap.org" + img_url
                    extra["avatar"] = img_url
            except Exception:
                pass
            return Result.taken(extra=extra)
        if "does not exist" in response.text:
            return Result.available()
        return Result.error()

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)