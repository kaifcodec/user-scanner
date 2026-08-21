import json
import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


NOT_FOUND = "The page you are looking for does not seem to exist anymore."
PROFILE_RE = re.compile(
    r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def validate_beacons(user: str) -> Result:
    url = f"https://beacons.ai/{quote(user, safe='')}"

    def process(response):
        for block in PROFILE_RE.findall(response.text):
            try:
                profile = json.loads(block)
            except json.JSONDecodeError:
                continue
            if not isinstance(profile, dict) or profile.get("@type") != "ProfilePage":
                continue

            person = profile.get("mainEntity")
            identifier = person.get("identifier") if isinstance(person, dict) else None
            if (
                not isinstance(identifier, str)
                or identifier.casefold() != user.casefold()
            ):
                return Result.error(
                    "Beacons profile did not match the requested username"
                )

            return Result.taken(
                extra={
                    "name": profile.get("name") or person.get("name"),
                    "description": profile.get("description"),
                    "social_links": person.get("sameAs") or None,
                    "featured_link": profile.get("significantLink"),
                },
                media={"avatar": profile.get("image") or person.get("image")},
            )

        if NOT_FOUND in response.text:
            return Result.available()

        return Result.error(f"Unexpected Beacons response: {response.status_code}")

    return impersonate_validate(url, process, allow_redirects=True)
