from user_scanner.core.orchestrator import generic_validate, Result

def validate_hashnode(user):
    url = f"https://hashnode.com/@{user}"
    show_url = url

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Language': "en-US,en;q=0.9",
        'Upgrade-Insecure-Requests': "1"
    }

    def process(response):
        if response.status_code == 200:
            if "Available for</h2>" in response.text:
                return Result.taken()
            else:
                return Result.available()

        return Result.error(f"Unexpected status code {response.status_code}, report it via GitHub issues.")

    return generic_validate(url, process, headers=headers, show_url=show_url)
