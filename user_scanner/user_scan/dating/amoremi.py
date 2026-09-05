import html
import re
from urllib.parse import quote

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

GENDERS = {"mehega": "male", "naisega": "female"}


def validate_amoremi(user: str) -> Result:
    username = user.strip()
    url = f"https://www.amoremi.ee/user/{quote(username, safe='')}"

    def process(response: httpx.Response) -> Result:
        if response.status_code == 404 and (
            "<title>Lehekülge ei leitud</title>" in response.text
            or f'Kasutajat nimega "{html.escape(username)}" ei eksisteeri.'
            in response.text
        ):
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        match = re.search(
            r'<div class="profile-title text-center">\s*'
            r'<div class=(?:"page-title"|page-title)>\s*([^<]+)',
            response.text,
        )
        if not match:
            return Result.error("Could not verify profile page")

        profile_user = html.unescape(match.group(1)).strip()
        if profile_user.casefold() != username.casefold():
            return Result.error("Profile response does not match the requested handle")

        extra: dict[str, object] = {}
        breadcrumb = re.search(
            r'<li class="breadcrumb-item active">\s*[^<]*?\s+(\d+)\s+a\.',
            response.text,
        )
        if breadcrumb:
            extra["age"] = int(breadcrumb.group(1))
        if profile_type := re.search(
            r'<a href="/tutvus/([^"/]+)">\s*([^<]+)</a>', response.text
        ):
            extra["profile_type"] = html.unescape(profile_type.group(2)).strip()
            if profile_gender := GENDERS.get(profile_type.group(1)):
                extra["gender"] = profile_gender
        if description := re.search(
            r"<div class=profile-description>.*?"
            r'<div class="short-desc">(.*?)</div>',
            response.text,
            re.DOTALL,
        ):
            extra["bio"] = _text(description.group(1))
        if seeking := re.search(
            r"Tutvun\s+(mehega|naisega)\s+(\d+)-(\d+)\s+a\.", response.text
        ):
            extra["looking_for"] = GENDERS[seeking.group(1)]
            extra["desired_age"] = f"{seeking.group(2)}-{seeking.group(3)}"
        if title := re.search(r"<title>(.*?)</title>", response.text, re.DOTALL):
            extra["headline"] = (
                html.unescape(title.group(1)).strip().removesuffix(f" - {profile_user}")
            )

        return Result.taken(extra=extra)

    return generic_validate(url, process, show_url=url)


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
