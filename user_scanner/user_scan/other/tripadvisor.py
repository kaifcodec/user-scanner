from user_scanner.core.orchestrator import generic_validate, Result


def validate_tripadvisor(user):
    url = f"https://www.tripadvisor.com/Profile/{user}"
    show_url = url

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0"
    }

    def process(response):
        if response.status_code == 200:
            return Result.taken()
        # Handles are case-canonicalized: a non-canonical casing 301-redirects
        # to the real profile, so a redirect back to /Profile/ still means the
        # account exists. Only a genuinely missing handle returns 404.
        if response.status_code in (301, 302):
            location = response.headers.get("location", "")
            if "/profile/" in location.lower():
                return Result.taken()
        if response.status_code == 404:
            return Result.available()
        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)
