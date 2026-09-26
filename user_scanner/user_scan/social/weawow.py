import html
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_weawow(user: str) -> Result:
    encoded_user = quote(user, safe="")
    url = f"https://weawow.com/m/{encoded_user}/profile"
    show_url = f"https://weawow.com/m/{encoded_user}"

    def process(response):
        text = response.text

        if (
            response.status_code == 200
            and '<link rel="canonical" href="https://weawow.com/i/aboutus"' in text
        ):
            return Result.available()

        username_match = re.search(r'class="userid">([^<]+)</a>', text)
        display_name = (
            html.unescape(username_match.group(1)).strip() if username_match else ""
        )
        if (
            response.status_code != 200
            or not username_match
            or display_name.casefold() != user.casefold()
        ):
            return Result.error(f"Unexpected response status: {response.status_code}")

        extra = {"display_name": display_name}
        fullname_match = re.search(r'<p class="margin-bottom30">([^<]*)</p>', text)
        if fullname_match:
            fullname = html.unescape(fullname_match.group(1)).strip()
            if fullname:
                extra["fullname"] = fullname

        links = re.findall(
            r'<a href="(https?://[^"]+)" target="_blank" rel="noopener">', text
        )
        if links:
            extra["links"] = [html.unescape(link) for link in links]

        for key, pattern in {
            "id": r'name="follow_(\d+)"',
            "followers": r'class="followers"><span>([\d,]+)</span>',
            "following": r'class="following"><span>([\d,]+)</span>',
            "photos": r'class="photo">.*?<span>Photos</span>([\d,]+)</a>',
            "marketplace_photos": r'class="marketplace">.*?<span>Marketplace</span>([\d,]+)</a>',
        }.items():
            match = re.search(pattern, text)
            if match:
                extra[key] = int(match.group(1).replace(",", ""))

        bio_match = re.search(r'class="m-profiledes">(.*?)</p>', text, re.DOTALL)
        if bio_match:
            bio = re.sub(r"<br\s*/?>", "\n", bio_match.group(1))
            bio = html.unescape(re.sub(r"<[^>]+>", "", bio)).strip()
            if bio:
                extra["bio"] = bio

        media = {}
        avatar_match = re.search(r'class="face-large"><img src="([^"]+)"', text)
        if avatar_match and not avatar_match.group(1).endswith("/facesample.jpg"):
            media["avatar"] = avatar_match.group(1)

        banner_match = re.search(r"background-image: url\(([^)]+)\)", text)
        if banner_match:
            media["banner"] = banner_match.group(1)

        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
