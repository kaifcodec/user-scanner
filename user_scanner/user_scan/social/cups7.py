from user_scanner.core.orchestrator import generic_validate, Result

def validate_7cups(user):
    url = f"https://www.7cups.com/@{user}"
    show_url = url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 202 or "x-amzn-waf-action" in response.headers:
            return Result.error("AWS WAF challenge triggered")

        if response.status_code == 404:
            return Result.available()

        if "Profile - 7 Cups" in response.text:
            return Result.taken()

        if "The content you're attempting to access could not be" in response.text:
            return Result.available()

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)
