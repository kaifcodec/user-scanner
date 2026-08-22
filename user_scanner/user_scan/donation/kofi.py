import html
import re

from user_scanner.core.orchestrator import Result, generic_validate


def _text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def validate_kofi(user: str) -> Result:
    url = f"https://ko-fi.com/{user}"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        page = response.text
        profile_marker = re.search(
            rf'<meta property="og:url" content="{re.escape(url)}(?:[/?][^"]*)?"', page
        )

        if profile_marker and 'id="displayName"' in page:
            extra = {}
            media = {}

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

            return Result.taken(extra=extra, media=media)

        if '<meta property="og:url" content="https://ko-fi.com/"' in page:
            return Result.available()

        return Result.error("Unexpected response body")

    return generic_validate(url, process, show_url=url, follow_redirects=True)
