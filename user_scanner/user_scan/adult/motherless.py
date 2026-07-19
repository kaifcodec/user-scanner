from user_scanner.core.orchestrator import generic_validate, Result

CHECK_URL = "https://motherless.xxx/register/checkusername"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://motherless.xxx",
    "Referer": "https://motherless.xxx/register",
}


def validate_motherless(user):
    show_url = f"https://motherless.xxx/m/{user}"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        body = response.text

        # The field check reuses "not-available" for both taken names and
        # rejected input (e.g. "Username is invalid.").
        if 'class="not-available"' in body:
            if "invalid" in body.lower():
                return Result.error("Username rejected by Motherless", url=show_url)
            return Result.taken(url=show_url)

        if 'class="available"' in body:
            return Result.available(url=show_url)

        return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

    return generic_validate(
        CHECK_URL, process, show_url=show_url, method="POST", data={"username": user}, headers=HEADERS
    )
