import html
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_nexusmods(user: str) -> Result:
    url = f"https://www.nexusmods.com/profile/{quote(user, safe='')}"

    def process(response):
        if response.status_code == 404 and r'\"c\":[\"\",\"profile\"' in response.text:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        heading = re.search(
            r'<h1[^>]*class="[^"]*text-heading-sm[^"]*"[^>]*>\s*([^<]+)\s*</h1>',
            response.text,
        )
        if not heading or html.unescape(heading.group(1)).strip().casefold() != user.casefold():
            return Result.error("Profile response did not match the requested username")

        extra = {}
        avatar = re.search(
            r'src="(https://avatars\.nexusmods\.com/[^"]+)"', response.text
        )
        if avatar:
            extra["avatar"] = html.unescape(avatar.group(1))

        for field, marker in (
            ("endorsements_given", "endorsements-given"),
            ("profile_views", "profile-views"),
            ("kudos", "kudos"),
            ("last_active", "last-active-date"),
            ("joined", "joined-date"),
        ):
            match = re.search(
                rf'data-e2eid="{marker}"[^>]*>\s*([^<]+)', response.text
            )
            if match:
                extra[field] = html.unescape(match.group(1)).strip()

        return Result.taken(extra=extra)

    return generic_validate(url, process, show_url=url, follow_redirects=True)
