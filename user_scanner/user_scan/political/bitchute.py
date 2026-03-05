from user_scanner.core.orchestrator import generic_validate, Result


def validate_bitchute(user):
    url = "https://api.bitchute.com/api/beta/channel"
    show_url = f"https://www.bitchute.com/channel/{user}/"
    payload = {"channel_id": user}
    headers = {"Content-Type": "application/json"}

    def process(response):
        if '"channel_id":' in response.text:
            return Result.taken()

        if '"errors":' in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, method="post", json=payload, headers=headers, show_url=show_url)
