from user_scanner.core.orchestrator import Result, make_request


def validate_devto(user):
    url = "https://dev.to/api/users/by_username"
    show_url = f"https://dev.to/{user}"

    try:
        response = make_request(url, params={"url": user}, follow_redirects=True)
        if response.status_code == 200:
            data = response.json()
            extra = {}
            if name := data.get("name"):
                extra["name"] = name
            if summary := data.get("summary"):
                extra["bio"] = summary.strip()
            if location := data.get("location"):
                extra["location"] = location
            if joined_at := data.get("joined_at"):
                extra["joined_at"] = joined_at
            if website := data.get("website_url"):
                extra["website"] = website
            if github := data.get("github_username"):
                extra["github"] = github
            if twitter := data.get("twitter_username"):
                extra["twitter"] = twitter

            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
