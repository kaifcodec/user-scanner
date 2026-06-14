from user_scanner.core.orchestrator import generic_validate, Result

def validate_githubgist(user):
    # Github Gists uses github users, so we can securely query the API
    url = f"https://api.github.com/users/{user}"
    show_url = f"https://gist.github.com/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            try:
                data = response.json()
                extra = {}
                if data.get("name"):
                    extra["name"] = data.get("name")
                if data.get("bio"):
                    extra["bio"] = data.get("bio")
                if data.get("location"):
                    extra["location"] = data.get("location")
                if data.get("public_gists") is not None:
                    extra["public_gists"] = data.get("public_gists")
                if data.get("created_at"):
                    extra["joined"] = data.get("created_at")
                
                return Result.taken(extra=extra)
            except Exception:
                return Result.taken()
                
        elif response.status_code == 403:
            return Result.error("Rate limited by GitHub API")

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github.v3+json"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
