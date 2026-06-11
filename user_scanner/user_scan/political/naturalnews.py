from user_scanner.core.orchestrator import generic_validate, Result
import re

def validate_naturalnews(user):
    url = f"https://naturalnews.com/author/{user}/"
    show_url = url

    def process(response):
        if '<div class="VideoPosts">' in response.text:
            extra = {}
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                clean_title = title_match.group(1).replace(" - NaturalNews.com", "").strip()
                extra["title"] = clean_title
            return Result.taken(extra=extra)

        if "The page you are looking for cannot be found" in response.text or response.status_code == 404:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
