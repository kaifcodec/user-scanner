from user_scanner.core.orchestrator import generic_validate, Result
import re

def validate_donatello(user):
    url = f"https://donatello.to/{user}"
    show_url = f"https://donatello.to/{user}"

    def process(response):
        if response.status_code == 200:
            extra = {}
            author_match = re.search(r'<meta name="author" content="([^"]+)">', response.text)
            if author_match:
                name = author_match.group(1).strip()
                if name.lower() != user.lower():
                    extra["name"] = name
            return Result.taken(extra=extra)
        elif response.status_code == 404:
            return Result.available()
        return Result.error(f"Unexpected status {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
