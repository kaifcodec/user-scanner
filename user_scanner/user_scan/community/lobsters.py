from user_scanner.core.orchestrator import generic_validate, Result

def validate_lobsters(user):
    url = f"https://lobste.rs/u/{user}.json"
    show_url = f"https://lobste.rs/u/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                extra = {}
                if data.get("about"):
                    extra["about"] = data.get("about")
                if data.get("created_at"):
                    extra["created_at"] = data.get("created_at")
                if data.get("karma") is not None:
                    extra["karma"] = data.get("karma")
                if data.get("github_username"):
                    extra["github_username"] = data.get("github_username")
                return Result.taken(extra=extra)
            except Exception:
                return Result.error("Unexpected response body, report it via GitHub issues.")
        elif response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected status code {response.status_code}")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)