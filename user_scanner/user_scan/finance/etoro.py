from user_scanner.core.orchestrator import generic_validate, Result

def validate_etoro(user):
    url = f"https://www.etoro.com/api/logininfo/v1.1/users/{user}"
    show_url = f"https://www.etoro.com/people/{user}"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.etoro.com/"
    }

    def process(response):
        if '"gcid":' in response.text:
            extra = {}
            try:
                data = response.json()
                first = data.get("firstName")
                last = data.get("lastName")
                if first or last:
                    name_parts = []
                    if first: name_parts.append(first.strip())
                    if last: name_parts.append(last.strip())
                    extra["name"] = " ".join(name_parts)

                bio = data.get("aboutMe")
                if bio:
                    extra["bio"] = bio.strip()
                else:
                    bio_short = data.get("aboutMeShort")
                    if bio_short:
                        extra["bio"] = bio_short.strip()

                avatars = data.get("avatars")
                if avatars and isinstance(avatars, list) and len(avatars) > 0:
                    extra["avatar"] = avatars[0]["url"]

                if data.get("isVerified"):
                    extra["is_verified"] = True
            except Exception:
                pass
            return Result.taken(extra=extra)

        if '"ErrorCode":"NotFound"' in response.text:
            return Result.available()

        if response.status_code == 403:
            return Result.error("Blocked by Cloudflare protection.")

        return Result.error("Unexpected API response format.")

    return generic_validate(url, process, headers=headers, show_url=show_url)

