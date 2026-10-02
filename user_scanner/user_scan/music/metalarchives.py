import re
from html import unescape
from urllib.parse import quote

from user_scanner.core.helpers import is_valid_email
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_metalarchives(user: str) -> Result:
    url = f"https://www.metal-archives.com/users/{quote(user, safe='')}"

    def process(response) -> Result:
        text = response.text
        if response.status_code == 404 and "Error 404 - user not found" in text:
            return Result.available()

        if response.status_code == 200 and 'id="user_info"' in text:
            extra: dict[str, str | bool | int] = {
                "profile_hidden": "profile information hidden to non-members" in text
            }
            if user_id := re.search(r"/user/tab-bands/id/(\d+)", text):
                extra["user_id"] = user_id.group(1)
            if email := re.search(r'<a[^>]+class="nospam"[^>]+rel="([^"]+)"', text):
                public_email = unescape(email.group(1))[::-1].replace("//", "@").replace("/", ".")
                if is_valid_email(public_email):
                    extra["public_email"] = public_email
            for label, value in re.findall(
                r"<dt>\s*([^<]+?):\s*</dt>\s*<dd[^>]*>(.*?)</dd>",
                text,
                re.DOTALL,
            ):
                value = unescape(re.sub(r"<[^>]+>", "", value)).strip()
                if value and label != "Email address":
                    extra[
                        "favorite_genres"
                        if label == "Favourite metal genre(s)"
                        else label
                    ] = value
            return Result.taken(extra=extra)

        return Result.error(f"Unexpected Metal Archives response (HTTP {response.status_code})")

    return impersonate_validate(url, process)
