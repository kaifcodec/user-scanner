from user_scanner.core.orchestrator import generic_validate, Result
import re

def validate_americanthinker(user):
    url = f"https://www.americanthinker.com/author/{user}/"
    show_url = url

    def process(response):
        if response.status_code == 200:
            extra = {}
            name_match = re.search(r'<h3 class="author_name">([^<]+)</h3>', response.text)
            if name_match:
                extra["name"] = name_match.group(1).strip()
            return Result.taken(extra=extra)
        elif response.status_code == 404:
            return Result.available()
        return Result.error(f"Unexpected status code {response.status_code}")

    return generic_validate(url, process, show_url=show_url, follow_redirects=False)
