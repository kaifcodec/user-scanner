import re
from html import unescape

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_lnkbio(user: str) -> Result:
    url = f"https://lnk.bio/{user}"

    def process(response):
        body = response.text

        def clean_text(value: str) -> str:
            return " ".join(unescape(re.sub(r"<[^>]+>", " ", value)).split())

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        if "Can't find this page" in body and "but it's not here!" in body:
            return Result.available()

        profile_page = re.search(
            r'<div(?=[^>]*\bclass="[^"]*\bpublic-container-inner\b)(?=[^>]*\bdata-page-id="PAGE_[^"]+")[^>]*>',
            body,
            re.IGNORECASE,
        )
        if not profile_page:
            return Result.error("Lnk.Bio profile markers were missing")

        avatar = re.search(
            r'<img(?=[^>]*\bid="profile_picture_catch_error")(?=[^>]*\bsrc="([^"]+)")[^>]*>',
            body,
            re.IGNORECASE,
        )
        extra = {}

        name = re.search(
            r'<[^>]*class="[^"]*\bpb-name\b[^"]*"[^>]*>(.*?)</[^>]+>',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if name and (name_text := clean_text(name.group(1))):
            extra["name"] = name_text

        bio = [
            clean_text(value)
            for value in re.findall(
                r'<span[^>]*class="[^"]*\bpb-bio\b[^"]*"[^>]*>(.*?)</span>\s*</div></div>',
                body,
                re.IGNORECASE | re.DOTALL,
            )
        ]
        if bio := [value for value in bio if value]:
            extra["bio"] = " ".join(bio)

        profile_username = re.search(
            r'<a[^>]*class="[^"]*\bpb-username\b[^"]*"[^>]*>(.*?)</a>',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        profile = profile_username or re.search(
            r'<a[^>]*data-type="TYPE_PROFILEPIC"[^>]*>', body, re.IGNORECASE
        )
        if profile:
            if profile_username and (
                username := clean_text(profile_username.group(1)).removeprefix("@")
            ).lower() != user.lower():
                extra["username"] = username

            for key, attribute in (
                ("profile_url", "href"),
                ("uid", "data-id"),
                ("timezone", "data-timezone"),
            ):
                value = re.search(rf'\b{attribute}="([^"]+)"', profile.group(), re.IGNORECASE)
                if value:
                    extra[key] = unescape(value.group(1))

        social_links = re.findall(
            r'<a(?=[^>]*\bclass="[^"]*\blb-icon-pub\b)(?=[^>]*\bhref="([^"]+)")[^>]*>',
            body,
            re.IGNORECASE,
        )
        if social_links:
            extra["social_links"] = [unescape(link) for link in social_links]

        page_url = re.search(r'\bdata-page-url="([^"]+)"', profile_page.group(), re.IGNORECASE)
        if page_url and not unescape(page_url.group(1)).lower().startswith(
            ("https://lnk.bio/", "http://lnk.bio/")
        ):
            extra["custom_domain"] = unescape(page_url.group(1))

        if "Verified by Lnk.Bio" in body:
            extra["verified"] = True

        return Result.taken(
            extra=extra, media={"avatar": unescape(avatar.group(1))} if avatar else {}
        )

    return generic_validate(url, process, show_url=url, follow_redirects=True)
