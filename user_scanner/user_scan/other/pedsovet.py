import html
import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


USERNAME_RE = re.compile(r"^[a-z0-9_@]+$", re.IGNORECASE)


def _strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def _profile_id(response_text: str) -> str | None:
    patterns = [
        r"/index/8-(\d+)",
        r"user-id=['\"](\d+)['\"]",
        r'\{uid:\s*"(\d+)"\}',
    ]
    for pattern in patterns:
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)

    return None


def _field(response_text: str, label: str) -> str | None:
    match = re.search(
        rf"<p>{re.escape(label)}:\s*(.*?)</p>",
        response_text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return _strip_tags(match.group(1))

    return None


def _avatar(response_text: str) -> str | None:
    match = re.search(
        r'<div class="user">\s*<center><img\s+src="([^"]+)"',
        response_text,
        re.IGNORECASE,
    )
    if not match:
        return None

    avatar = html.unescape(match.group(1)).strip()
    if avatar.startswith("//"):
        return "https:" + avatar
    if avatar.startswith("/"):
        return "https://pedsovet.su" + avatar
    return avatar


def _last_login(response_text: str) -> str | None:
    match = re.search(
        r"Последний вход\s*([^<]+)",
        response_text,
        re.IGNORECASE,
    )
    if match:
        return html.unescape(match.group(1)).strip()

    return None


def _about(response_text: str) -> str | None:
    match = re.search(
        r'<div class="osebe">О себе</div>.*?<p class="clr">(.*?)</p>',
        response_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None

    about = _strip_tags(match.group(1))
    if about == "Пользователь пока ничего не сообщил о себе.":
        return None
    return about


def _profile_extra(response_text: str, login: str) -> dict:
    profile_id = _profile_id(response_text)
    profile_url = f"https://pedsovet.su/index/8-{profile_id}" if profile_id else None

    return {
        "id": profile_id,
        "login": login,
        "group": _field(response_text, "Группа пользователей"),
        "registered": _field(response_text, "Регистрация"),
        "last_login": _last_login(response_text),
        "avatar": _avatar(response_text),
        "profile_url": profile_url,
        "about": _about(response_text),
    }


def validate_pedsovet(user: str) -> Result:
    user = user.strip()
    url = f"https://pedsovet.su/index/8-0-{user}"

    if not user:
        return Result.error("Username cannot be empty", url=url)

    if not USERNAME_RE.match(user):
        return Result.error(
            "Usernames can only contain letters, numbers, underscores and at signs",
            url=url,
        )

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }

    def process(response):
        response_text = response.text

        if "Пользователь не найден" in response_text:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        login_match = re.search(
            r"<p>Логин:\s*([^<]+)</p>",
            response_text,
            re.IGNORECASE,
        )
        found_login = html.unescape(login_match.group(1)).strip() if login_match else None
        has_profile_markers = (
            "Группа пользователей:" in response_text
            and "Регистрация:" in response_text
            and "Ссылка на профиль:" in response_text
        )

        if found_login and found_login.lower() == user.lower() and has_profile_markers:
            return Result.taken(extra=_profile_extra(response_text, found_login))

        return Result.error("Unexpected response body")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=url,
        follow_redirects=True,
    )
