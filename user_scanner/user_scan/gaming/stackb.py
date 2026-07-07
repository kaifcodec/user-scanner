import html
import json
import re
from urllib.parse import quote

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_stackb(user: str) -> Result:
    user = user.lower()
    profile_url = f"https://stackb.net/@{user}"
    url = f"https://stackb.net/@{quote(user, safe='')}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }

    def process(response):
        response_text = response.text

        if response.status_code == 404 and (
            "Страница не найдена" in response_text
            or re.search(r">\s*404\s*<", response_text)
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        profile = {}
        for json_match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', response_text, re.DOTALL):
            try:
                data = json.loads(html.unescape(json_match.group(1)))
            except json.JSONDecodeError:
                continue

            if data.get("@type") == "ProfilePage":
                entity = data.get("mainEntity")
                if isinstance(entity, dict):
                    profile = entity
                break

        og_type_match = re.search(r'<meta [^>]*property=["\']og:type["\'][^>]*content=["\']([^"\']*)', response_text, re.IGNORECASE)
        og_type = html.unescape(og_type_match.group(1)).strip() if og_type_match else None

        canonical_match = re.search(r'<link [^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)', response_text, re.IGNORECASE)
        canonical_url = html.unescape(canonical_match.group(1)).strip() if canonical_match else None

        if (
            og_type == "profile"
            and canonical_url == profile_url
            and profile.get("identifier") == f"@{user}"
        ):
            extra = {}
            description_match = re.search(r'<meta [^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']*)', response_text, re.IGNORECASE)
            stats_text = html.unescape(description_match.group(1)).strip() if description_match else None

            if name := profile.get("name"): extra["display_name"] = name
            if description := profile.get("description"): extra["bio"] = description
            if image := profile.get("image"): extra["avatar"] = image

            if stats_text:
                if rank_match := re.search(r"Ранг:\s*([^\.]+)", stats_text):
                    extra["rank"] = rank_match.group(1).strip()
                if followers_match := re.search(r"Подписчики:\s*(\d+)", stats_text):
                    extra["followers"] = int(followers_match.group(1))

            extra["profile_url"] = profile_url
            return Result.taken(extra=extra)

        return Result.error("Unexpected response body")

    return generic_validate(
        url,
        process,
        headers=headers,
        show_url=url,
        follow_redirects=True,
    )
