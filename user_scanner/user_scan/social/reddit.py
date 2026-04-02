import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

def validate_reddit(user):
    url = f"https://www.reddit.com/user/{user}/about.json"
    show_url = f"https://www.reddit.com/user/{user}/"

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 429:
            return Result.error("Rate limit exceeded")

        if response.status_code == 200:
            try:
                data = response.json()

                if data.get("error") == 404 or data.get("message") == "Not Found":
                    return Result.available()

                if data.get("kind") == "t2" or "data" in data:
                    return Result.taken()

            except (json.JSONDecodeError, KeyError):
                return Result.error("Malformed JSON response, report it on Github")

        return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
