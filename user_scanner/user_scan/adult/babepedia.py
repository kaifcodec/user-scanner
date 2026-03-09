from user_scanner.core.orchestrator import generic_validate, Result

def validate_babepedia(user):
    url = f"https://www.babepedia.com/user/{user}"
    show_url = f"https://www.babepedia.com/user/{user}"

    def process(response):
        if response.status_code == 200 and "'s Profile</title>" in response.text:
            return Result.taken()
        
        if response.status_code == 404 or "Profile not found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues")

    return generic_validate(url, process, show_url=show_url)
