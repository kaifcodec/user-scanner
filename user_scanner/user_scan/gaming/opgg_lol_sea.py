import html
import re

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

REGION = "sea"


def validate_opgg_lol_sea(user: str) -> Result:
    url = "https://op.gg/lol/summoners/search"
    show_url = "https://op.gg/lol/summoners/sea"

    def process(response):
        if response.status_code != 200:
            return Result.error(
                f"Unexpected response status: {response.status_code}", url=show_url
            )

        page = response.text
        anchor = re.search('href="/lol/summoners/sea/([^"]*)"', page)

        if anchor:
            card = page[anchor.start():anchor.start() + 2000]
            extra = {}
            media = {}

            riot_id = re.search(r'alt="([^"]+)"', card)
            if riot_id:
                extra["riot_id"] = riot_id.group(1)

            level = re.search(r'text-white">(\d+)</div>', card)
            if level:
                extra["level"] = level.group(1)

            avatar = re.search(r'src="([^"]+)"', card)
            if avatar:
                media["avatar"] = html.unescape(avatar.group(1))

            profile_url = f"https://op.gg/lol/summoners/{REGION}/{anchor.group(1)}"
            return Result.taken(extra=extra, media=media, url=profile_url)

        if ">No search results for" in page or "found in other regions.</h1>" in page:
            return Result.available(url=show_url)

        return Result.error("OP.GG answered no readable search page", url=show_url)

    return generic_validate(url, process, params={"q": user, "region": REGION})
