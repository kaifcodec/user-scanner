from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_soundcloud(user):
    url = f"https://soundcloud.com/{user}"
    show_url = f"https://soundcloud.com/{user}"

    def process(response):
        if response.status_code == 403:
            return Result.error("[403] Request forbidden try using proxy or VPN")

        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200:
            text = response.text

            if f"soundcloud://users:{user}" in text:
                return Result.taken()
            if f'"username":"{user}"' in text:
                return Result.taken()
            if "soundcloud://users:" in text and '"username":"' in text:
                return Result.taken()

            return Result.error("Unexpected response, report it via GitHub issues")

        return Result.error("Unknown Error report it via GitHub issues")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
