import json
import re

from user_scanner.core.orchestrator import Result, generic_validate


def validate_codecademy(user):
    url = f"https://www.codecademy.com/profiles/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            try:
                # Codecademy embeds profile data in a Next.js JSON blob
                match = re.search(
                    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                    response.text,
                )
                if match:
                    data = json.loads(match.group(1))
                    user_data = (
                        data.get("props", {}).get("pageProps", {}).get("profile", {})
                    )
                    extra = {
                        "name": user_data.get("name"),
                        "bio": user_data.get("bio"),
                        "location": user_data.get("location"),
                        "joined": user_data.get("createdAt"),
                    }
                    return Result.taken(extra=extra)

                # If we couldn't parse it but it's 200, assume taken but no extra data
                return Result.taken()
            except Exception:
                return Result.taken()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=url, headers=headers)
