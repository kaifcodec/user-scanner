import html
import re
from urllib.parse import quote, urljoin, urlparse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def _text(markup: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def validate_comicvine(user: str) -> Result:
    url = f"https://comicvine.gamespot.com/profile/{quote(user, safe='')}/"

    def process(response):
        document = response.text
        if response.status_code == 404 and (
            "<title>404: Not Found - Comic Vine</title>" in document
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        if f'<link rel="canonical" href="{url}"' not in document:
            return Result.error("Profile response did not match the requested username")

        extra = {}
        media = {}

        name = re.search(
            r'<section class="profile-title">\s*<h1>([^<]+)</h1>', document
        )
        if name:
            extra["display_name"] = _text(name.group(1))

        status = re.search(r'<h4 class="js-status-message">(.*?)</h4>', document)
        if status and (
            status_text := _text(status.group(1))
        ) != "This user has not updated recently.":
            extra["status"] = status_text

        about = re.search(
            r'<div class="about-me">.*?<article[^>]*>(.*?)</article>',
            document,
            re.DOTALL,
        )
        if about:
            extra["bio"] = _text(about.group(1))
            links = []
            for href in re.findall(r'href=["\']([^"\']+)', about.group(1)):
                link = urljoin(url, html.unescape(href))
                host = urlparse(link).hostname or ""
                if link.startswith(("http://", "https://")) and not host.endswith(
                    ("gamespot.com", "cbsistatic.com")
                ):
                    links.append(link)
            if links:
                extra["links"] = list(dict.fromkeys(links))

        for field, label in (("joined", "Date joined"), ("alignment", "Alignment")):
            value = re.search(
                rf"<strong>{label}:</strong>\s*([^<]+)", document
            )
            if value:
                extra[field] = _text(value.group(1))

        stats = re.search(
            r'<section class="profile-follow">.*?<tr>\s*'
            r"<td>([^<]*)</td>\s*<td>([^<]*)</td>\s*"
            r'<td><a[^>]*>([^<]*)</a></td>\s*<td><a[^>]*>([^<]*)</a></td>',
            document,
            re.DOTALL,
        )
        if stats:
            for key, value in zip(
                ("forum_posts", "wiki_points", "following", "followers"),
                stats.groups(),
            ):
                extra[key] = value.strip()

        for page, count in re.findall(
            r'href="/profile/[^/]+/(images|lists|reviews)/"[^>]*>\s*'
            r"[^<]*\((\d+)\)\s*</a>",
            document,
        ):
            extra[f"{page.removesuffix('s')}_count"] = int(count)

        avatar = re.search(
            r'<section class="profile-avatar">\s*'
            r'<div class="([^"]*\bavatar\b[^"]*)".*?<img src="([^"]+)"',
            document,
            re.DOTALL,
        )
        if avatar:
            badges = [badge for badge in avatar.group(1).split() if badge != "avatar"]
            if badges:
                extra["membership_badges"] = badges
            media["avatar"] = html.unescape(avatar.group(2))

        profile_image = re.search(
            r'<div class="profile-image">.*?<img src="([^"]+)"',
            document,
            re.DOTALL,
        )
        if profile_image:
            media["profile_image"] = html.unescape(profile_image.group(1))

        banner = re.search(
            r'class="kubrick kubrick-profile[^>]+style="background-image: url\(([^)]+)\)',
            document,
        )
        if banner:
            media["banner"] = html.unescape(banner.group(1))

        wiki_pages = []
        for count, name, page_type in re.findall(
            r'class="img data-count" data-count="(\d+)".*?'
            r"<h4>(.*?)</h4>\s*<p>([^<]+)</p>",
            document,
            re.DOTALL,
        ):
            if clean_name := _text(name):
                wiki_pages.append(
                    f"{clean_name} ({page_type.strip()}, {count} edits)"
                )
        if wiki_pages:
            extra["top_wiki_pages"] = wiki_pages

        lists = [
            _text(item)
            for item in re.findall(
                r'<dt>\s*<a href="/profile/[^/]+/lists/[^>]+>(.*?)</a>\s*</dt>',
                document,
                re.DOTALL,
            )
        ]
        if lists:
            extra["lists"] = lists

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(
        url,
        process,
        impersonate="safari2601",
    )
