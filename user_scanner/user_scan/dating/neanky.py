import html
import re
from urllib.parse import quote, unquote, urljoin

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_neanky(user: str) -> Result:
    username = user.strip()
    url = f"https://neanky.ee/user/{quote(username, safe='')}"

    def process(response: httpx.Response) -> Result:
        if (
            response.status_code == 404
            and "Kasutajat ei leitud | Neanky suhtlusvõrgustik" in response.text
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        pending = re.search(
            r"Soovitud kasutaja ei ole hetkel veel aktiveeritud!<br>\s*"
            r"Konto registreeritud:\s*([^<]+)<br>",
            response.text,
        )
        canonical = re.search(
            r'<link rel="canonical" href="https://neanky\.ee/user/([^"?#]+)">',
            response.text,
        )
        if pending and canonical:
            profile_user = html.unescape(unquote(canonical.group(1))).strip()
            if profile_user.casefold() != username.casefold():
                return Result.error(
                    "Profile response does not match the requested handle"
                )
            return Result.taken(
                extra={
                    "account_status": "pending_activation",
                    "registered_at": pending.group(1).strip(),
                }
            )

        match = re.search(
            r'<h1 class="u-box-name-txt-b text-white">(.*?)</h1>',
            response.text,
            re.DOTALL,
        )
        if not match:
            return Result.error("Could not verify profile page")

        profile_user = _text(match.group(1))
        if profile_user.casefold() != username.casefold():
            return Result.error("Profile response does not match the requested handle")

        extra: dict[str, object] = {}
        if name := re.search(r"Nimi:\s*<strong>(.*?)</strong>", response.text):
            extra["name"] = _text(name.group(1))
        if gender := re.search(r"Sugu:\s*<img[^>]*>\s*([^<]+)<br", response.text):
            extra["gender"] = html.unescape(gender.group(1)).strip()
        if user_id := re.search(r'\bvar vsID="(\d+)"', response.text):
            extra["user_id"] = int(user_id.group(1))
        if online_status := re.search(
            r'<span[^>]+title="(online|offline)"', match.group(1)
        ):
            extra["online_status"] = online_status.group(1)
        media: dict[str, str] = {}
        avatar = re.search(
            r"u-box-avatar-Pic[^>]+background-image:url\([\'\"]?([^\'\")]+)",
            response.text,
        )
        if avatar and not avatar.group(1).endswith("/images/avatar.svg"):
            media["avatar"] = urljoin("https://neanky.ee", avatar.group(1))
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url)


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
