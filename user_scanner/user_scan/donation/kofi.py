import html
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def _text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def validate_kofi(user: str) -> Result:
    url = f"https://ko-fi.com/{user}"
    if "." in user:
        return Result.available("Username cannot contain periods", url=url)

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        page = response.text

        # If redirected to the home page, the username does not exist
        if '<meta property="og:url" content="https://ko-fi.com/"' in page or response.url.rstrip("/") == "https://ko-fi.com":
            return Result.available(url=url)

        profile_marker = re.search(
            rf'<meta property="og:url" content="{re.escape(url)}(?:[/?][^"]*)?"', page, re.IGNORECASE
        )

        if (profile_marker or f"ko-fi.com/{user.lower()}" in page.lower()) and 'id="displayName"' in page:
            extra: dict[str, str | int | list[str]] = {}
            media: dict[str, str] = {}

            if match := re.search(
                r'<span id="displayName">\s*([^<]+?)\s*</span>', page
            ):
                extra["name"] = _text(match.group(1))
            if match := re.search(r'\bdata-reported-page-id="([^"]+)"', page):
                extra["id"] = match.group(1)
            if match := re.search(
                r'class="kfds-c-profile-link-handle[^"]*"[^>]*>\s*'
                r"([\d,]+)\s+(Followers|Supporters)\s*</",
                page,
            ):
                extra[match.group(2).lower()] = int(match.group(1).replace(",", ""))
            if match := re.search(
                r'id="expanded-page"[^>]*>\s*<p[^>]*>(.*?)</p>', page, re.DOTALL
            ):
                extra["bio"] = _text(match.group(1))

            categories = [
                _text(value)
                for value in re.findall(
                    r'<span class="label-tag">\s*(.*?)\s*</span>', page, re.DOTALL
                )
            ]
            if categories:
                extra["categories"] = list(dict.fromkeys(categories))

            features = [
                _text(value)
                for value in re.findall(
                    r'class="kfds-c-profile-tab-box"[^>]*>.*?<label[^>]*>(.*?)</label>',
                    page,
                    re.DOTALL,
                )
            ]
            if features:
                extra["features"] = list(dict.fromkeys(features))

            links = re.findall(
                r'<a(?=[^>]*\bid="socialLink_)[^>]*\bhref="([^"]+)"',
                page,
            )
            if match := re.search(
                r'<div class="social-link[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"',
                page,
                re.DOTALL,
            ):
                links.insert(0, match.group(1))
            if links:
                extra["links"] = list(dict.fromkeys(map(html.unescape, links)))

            if match := re.search(r'<img id="profilePicture"[^>]+src="([^"]+)"', page):
                media["avatar"] = html.unescape(match.group(1))

            return Result.taken(extra=extra, media=media, url=url)

        return Result.error("Unexpected response body", url=url)

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)
