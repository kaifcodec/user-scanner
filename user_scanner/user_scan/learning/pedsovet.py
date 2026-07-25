import html
import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_pedsovet(user: str) -> Result:
    url = f"https://pedsovet.su/index/8-0-{user}"

    if not re.match(r"^[a-z0-9_@]+$", user, re.IGNORECASE):
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

        login_match = re.search(r"<p>Логин:\s*([^<]+)</p>", response_text, re.IGNORECASE)
        found_login = html.unescape(login_match.group(1)).strip() if login_match else None

        if (
            found_login
            and found_login.lower() == user.lower()
            and "Ссылка на профиль:" in response_text
        ):
            extra = {"login": found_login}

            if id_match := re.search(r"/index/8-(\d+)", response_text):
                extra["id"] = id_match.group(1)
                extra["profile_url"] = f"https://pedsovet.su/index/8-{id_match.group(1)}"

            for label, key in (
                ("Группа пользователей", "group"),
                ("Регистрация", "registered"),
            ):
                if field_match := re.search(rf"<p>{re.escape(label)}:\s*(.*?)</p>", response_text, re.IGNORECASE | re.DOTALL):
                    value = re.sub(r"<[^>]+>", "", field_match.group(1))
                    extra[key] = html.unescape(value).strip()

            if last_login_match := re.search(r"Последний вход\s*([^<]+)", response_text, re.IGNORECASE):
                extra["last_login"] = html.unescape(last_login_match.group(1)).strip()

            if avatar_match := re.search(
                r'<div class="user">\s*<center><img\s+src="([^"]+)"', response_text, re.IGNORECASE
            ):
                avatar = html.unescape(avatar_match.group(1)).strip()
                if avatar.startswith("//"):
                    avatar = "https:" + avatar
                elif avatar.startswith("/"):
                    avatar = "https://pedsovet.su" + avatar
                extra["avatar"] = avatar

            if about_match := re.search(
                r'<div class="osebe">О себе</div>.*?<p class="clr">(.*?)</p>', response_text, re.IGNORECASE | re.DOTALL
            ):
                about = re.sub(r"<[^>]+>", "", about_match.group(1))
                about = html.unescape(about).strip()
                if about != "Пользователь пока ничего не сообщил о себе.":
                    extra["about"] = about

            return Result.taken(extra=extra)

        return Result.error("Unexpected response body")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=url,
        follow_redirects=True,
    )
