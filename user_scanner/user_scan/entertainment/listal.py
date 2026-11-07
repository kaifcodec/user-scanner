import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result


def validate_listal(user: str) -> Result:
    if not re.match(r"^[A-Za-z0-9_-]+$", user):
        return Result.error("Invalid username format for Listal")

    url = f"https://{user}.listal.com/"
    show_url = f"https://{user}.listal.com/"

    def process(response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        m = re.search(r"<title>([^<]+?)(?:'s stuff)? on Listal</title>", response.text)
        if m and m.group(1).strip().lower() == user.lower():
            extra: dict[str, str] = {}
            media: dict[str, str] = {}

            pt = re.search(r"<b>Points:</b>\s*(?:<a[^>]*>)?(\d+)", response.text)
            if pt:
                extra["points"] = pt.group(1)

            fl = re.search(r"(\d+) Followers</a>", response.text)
            if fl:
                extra["followers"] = fl.group(1)

            av = re.search(r'<img[^>]*src="(https://lthumb\.lisimg\.com/[^"]+)"', response.text)
            if av:
                media["avatar"] = av.group(1)

            return Result.taken(extra=extra, media=media)

        if "Listal - List the stuff you love!" in response.text:
            return Result.available()

        return Result.error("Unexpected response body from Listal")

    return impersonate_validate(
        url,
        process,
        show_url=show_url,
        impersonate="chrome",
        allow_redirects=True,
    )
