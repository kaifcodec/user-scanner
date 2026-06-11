from user_scanner.core.orchestrator import generic_validate, Result
import re

def validate_newamerica(user):
    url = f"https://www.newamerica.org/our-people/{user}/"
    show_url = url

    def process(response):
        if response.status_code == 200 and "Page not found" not in response.text:

            final_url = str(response.url)
            if f"/people/{user}/" in final_url or f"/our-people/{user}/" in final_url:
                extra = {}
                name_match = re.search(r'<h1 class="header2-name"[^>]*>([^<]+)</h1>', response.text)
                if name_match:
                    extra["name"] = name_match.group(1).strip()
                return Result.taken(extra=extra)

        if "Page not found" in response.text or response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected response body, status {response.status_code}")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
