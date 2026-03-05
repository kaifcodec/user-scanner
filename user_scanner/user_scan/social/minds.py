from user_scanner.core.orchestrator import generic_validate, Result


def validate_minds(user):
    url = f"https://www.minds.com/api/v3/register/validate?username={user}"
    show_url = f"https://www.minds.com/{user}"

    def process(response):
        if response.status_code == 200 and '"valid":false' in response.text:
            return Result.taken()

        if '"valid":true' in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
