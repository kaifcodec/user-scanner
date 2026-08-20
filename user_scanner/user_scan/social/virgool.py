import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.nextjs import iter_next_app_flight_chunks
from user_scanner.core.orchestrator import Result, generic_validate


def validate_virgool(user):
    url = f"https://virgool.io/@{user}"
    headers = {"User-Agent": get_random_user_agent()}

    def process(response):
        if response.status_code == 200:
            extra = {}
            flight = next(
                (
                    chunk
                    for chunk in iter_next_app_flight_chunks(response.text)
                    if '"followersCount"' in chunk
                ),
                "",
            )

            fc_match = re.search(r'"followersCount":(\d+)', flight)
            if fc_match:
                extra["follower_count"] = int(fc_match.group(1))

            name_match = re.search(r'"name":"([^"]+)"', flight)
            if name_match:
                extra["fullname"] = name_match.group(1)

            bio_match = re.search(r'"bio":"([^"]+)"', flight)
            if bio_match:
                extra["bio"] = bio_match.group(1)
            return Result.taken(extra=extra)
        if response.status_code == 404:
            return Result.available()
        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=url, headers=headers)
