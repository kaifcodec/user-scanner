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
            return Result.taken()

        if '"ErrorCode":"NotFound"' in response.text:
            return Result.available()

        if response.status_code == 403:
            return Result.error("Blocked by Cloudflare protection.")

        return Result.error("Unexpected API response format.")

    return generic_validate(url, process, headers=headers, show_url=show_url)
