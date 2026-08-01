from user_scanner.core.orchestrator import generic_validate, Result

def validate_codepen(user):
    url = f"https://codepen.io/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200:
            marker_og = f'og:url" content="https://codepen.io/{user}'
            marker_title = f'(@{user})'
            if marker_og in response.text or marker_title in response.text:
                return Result.taken(extra={"profile": url})
            return Result.error("Ambiguous response body, report it via GitHub issues.")

        return Result.error(f"Unexpected status code {response.status_code}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    return generic_validate(url, process, show_url=show_url, headers=headers)