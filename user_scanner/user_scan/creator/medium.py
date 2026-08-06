import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

# Medium answers unknown handles with HTTP 200 and renders its 404 view, so the
# status code carries no verdict — only these body markers do.
NOT_FOUND_MARKERS = (">PAGE NOT FOUND<", "Out of nothing, something.")


def validate_medium(user):
    url = f"https://medium.com/@{user}"
    show_url = url

    def process(response):
        html = response.text

        # Medium resolves handles case-insensitively but echoes the canonical
        # casing here, so the served profile must be matched, not the request.
        served = re.search(r'property="profile:username" content="([^"]*)"', html)

        if served and served.group(1).lower() == user.lower():
            extra = {}
            media = {}

            person = _person_ld_json(html)
            name = person.get("name")
            if name:
                extra["fullname"] = name

            bio = person.get("description")
            if bio:
                extra["bio"] = bio

            # Anchored to this profile's own followers link — the sidebar
            # carries the same markup for recommended authors.
            followers = re.search(
                rf'href="/@{re.escape(served.group(1))}/followers[^"]*"[^>]*>([\d.,]+[KM]?)\s+followers',
                html,
            )
            if followers:
                extra["followers"] = followers.group(1)

            avatar = re.search(r'property="og:image" content="([^"]+)"', html)
            if avatar:
                media["avatar"] = avatar.group(1)

            return Result.taken(extra=extra, media=media)

        if any(marker in html for marker in NOT_FOUND_MARKERS):
            return Result.available()

        return Result.error(f"Unexpected response body (HTTP {response.status_code})")

    # Accounts with a custom subdomain 301 to {user}.medium.com; the profile
    # markers only exist after that hop. Unknown handles never redirect.
    return impersonate_validate(url, process, show_url=show_url, allow_redirects=True)


def _person_ld_json(html: str) -> dict:
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Person":
            return data
    return {}
