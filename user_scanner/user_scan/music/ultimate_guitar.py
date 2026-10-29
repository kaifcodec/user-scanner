import re
from datetime import datetime, timezone

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_ultimate_guitar(user: str) -> Result:
    url = f"https://www.ultimate-guitar.com/u/{user}"

    def process(response):
        if response.status_code == 410:
            return Result.available()
        if response.status_code == 200:
            m = re.search(r"<title>([^<]+) \| Ultimate-Guitar\.Com</title>", response.text)
            if m and m.group(1).strip().lower() == user.lower():
                extra, media = {}, {}
                t = re.search(r"usertitle&quot;:&quot;([^&]+)&quot;", response.text)
                if t: extra["usertitle"] = t.group(1)
                fc = re.search(r"follower_count&quot;:(\d+)", response.text)
                if fc: extra["followers"] = fc.group(1)
                fg = re.search(r"following_count&quot;:(\d+)", response.text)
                if fg: extra["following"] = fg.group(1)
                iq = re.search(r"iq&quot;:(\d+)", response.text)
                if iq: extra["iq"] = iq.group(1)
                dr = re.search(r"date_registered&quot;:(\d+)", response.text)
                if dr:
                    extra["joined"] = datetime.fromtimestamp(
                        int(dr.group(1)), tz=timezone.utc
                    ).strftime("%Y-%m-%d")
                city = re.search(r"city&quot;:&quot;([^&]*)&quot;", response.text)
                if city and city.group(1): extra["city"] = city.group(1)
                country = re.search(r"country_name&quot;:&quot;([^&]*)&quot;", response.text)
                if country and country.group(1): extra["location"] = country.group(1)
                va = re.search(r"is_avatar_exists&quot;:(true|false)", response.text)
                if va and va.group(1) == "true":
                    av = re.search(
                        r"avatar&quot;:&quot;(https://www\.ultimate-guitar\.com/static[^\s&quot;]+)&quot;",
                        response.text,
                    )
                    if av: media["avatar"] = av.group(1).replace("&amp;", "&")
                return Result.taken(extra=extra, media=media)
        return Result.error(f"Unexpected response status: {response.status_code}")

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)
