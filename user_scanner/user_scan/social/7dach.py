import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_7dach(user: str) -> Result:
    url = f"https://7dach.ru/profile/{user}"
    show_url = url

    def process(response) -> Result:
        if response.status_code == 200 and ("profile-data" in response.text or "profile-section-title" in response.text):
            extra: dict[str, str] = {}
            media: dict[str, str] = {}
            html = response.text

            name_match = re.search(r'<div class="profile-section-title\s*">([^<]+)</div>', html)
            if name_match:
                extra["name"] = name_match.group(1).strip()

            place_match = re.search(r'data-user-place="([^"]+)"', html)
            if place_match:
                extra["location"] = place_match.group(1).strip()

            avatar_match = re.search(r'data-user-avatar="([^"?]+)', html)
            if avatar_match:
                media["avatar"] = avatar_match.group(1).strip()

            joined_match = re.search(
                r'Зарегистрирован</span>\s*<span class="user-property__description">([^<]+)</span>',
                html,
            )
            if joined_match:
                extra["joined"] = joined_match.group(1).strip()

            return Result.taken(extra=extra, media=media)

        if response.status_code == 404 or "Ошибка" in response.text:
            return Result.available()

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
