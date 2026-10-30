import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_planetminecraft(user: str) -> Result:
    url = f"https://www.planetminecraft.com/member/{user}"

    def process(response):
        if response.status_code == 410:
            return Result.available()
        if response.status_code == 200:
            m = re.search(r"<title>([^<]+) on Planet Minecraft</title>", response.text)
            if m and m.group(1).strip().lower() == user.lower():
                extra, media = {}, {}
                h = re.search(r"<h1[^>]*>([^<]+)</h1>", response.text)
                if h: extra["username"] = h.group(1).strip()
                lv = re.search(r"Level (\d+)", response.text)
                if lv: extra["level"] = lv.group(1)
                rk = re.search(r'member-rank-class">([^<]+)</span>', response.text)
                if rk: extra["rank"] = rk.group(1).strip()
                mid = re.search(r"data-mid=['\"]?(\d+)", response.text)
                if mid: extra["member_id"] = mid.group(1)
                sub = re.search(r'num_subscribers">(\d+)', response.text)
                if sub: extra["followers"] = sub.group(1)
                av = re.search(
                    r"https://static\.planetminecraft\.com/files/avatar/\d+_\d+\.png",
                    response.text,
                )
                if av: media["avatar"] = av.group(0)
                return Result.taken(extra=extra, media=media)
        return Result.error(f"Unexpected response status: {response.status_code}")

    return impersonate_validate(url, process, show_url=url)
