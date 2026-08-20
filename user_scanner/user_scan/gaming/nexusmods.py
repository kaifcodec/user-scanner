import html
import json
import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import iter_next_app_flight_chunks
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
        media = {}
        avatar = re.search(
            r'<meta property="og:image" content="([^"]+)"', response.text
        )
        if avatar:
            media["avatar"] = html.unescape(avatar.group(1))
            user_id = re.search(r"/(\d+)/100$", media["avatar"])
            if user_id:
                extra["user_id"] = int(user_id.group(1))

        for field, marker in (
            ("unique_downloads", "unique-download-count"),
            ("endorsements_given", "endorsements-given"),
            ("profile_views", "profile-views"),
            ("kudos", "kudos"),
        ):
            match = re.search(
                rf'data-e2eid="{marker}"[^>]*>\s*([^<]+)', response.text
            )
            if match:
                extra[field] = html.unescape(match.group(1)).strip()

        for field, marker in (
            ("last_active", "last-active-date"),
            ("joined", "joined-date"),
        ):
            match = re.search(
                rf'data-e2eid="{marker}"[^>]*dateTime="([^"]+)"', response.text
            )
            if match:
                extra[field] = match.group(1)

        try:
            flight = next(
                (
                    chunk
                    for chunk in iter_next_app_flight_chunks(response.text)
                    if "UserByName" in chunk
                ),
                "",
            )
            member_id = flight.index('"memberId":')
            start = flight.rfind('"data":', 0, member_id) + len('"data":')
            profile = json.JSONDecoder().raw_decode(flight[start:])[0]
            extra.update(
                {
                    "country": profile.get("country"),
                    "posts": profile.get("posts"),
                    "recognized_author": profile.get("recognizedAuthor"),
                    "membership_roles": ", ".join(
                        profile.get("membershipRoles") or []
                    ),
                    "donations_enabled": profile.get("donationsEnabled"),
                    "about": html.unescape(profile.get("about") or "").strip(),
                    "paypal_email": profile.get("paypal"),
                }
            )
        except (AttributeError, ValueError, json.JSONDecodeError):
            pass

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)
