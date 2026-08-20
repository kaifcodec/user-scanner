import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.result import Result


def validate_linktree(user: str) -> Result:
    url = f"https://linktr.ee/{user}"

    def process(response):
        html = response.text

        data = parse_next_pages_data(html) or {}
        page_props = data.get("props", {}).get("pageProps", {})

        if response.status_code == 404:
            if (
                data.get("page") == "/_error" and page_props.get("statusCode") == 404
            ) or "Linktree | Page Not Found" in html:
                return Result.available()
            return Result.error("Unrecognized Linktree not-found response")

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        banned_user = data.get("query", {}).get("username")
        if data.get("page") == "/status/blocked" and (
            isinstance(banned_user, str) and banned_user.lower() == user.lower()
        ):
            return Result.taken(extra={"banned": True})

        account = page_props.get("account", {})
        embedded_user = page_props.get("username") or account.get("username")
        canonical_match = re.search(
            r'<(?:link[^>]*rel="canonical"[^>]*href|meta[^>]*property="og:url"[^>]*content)="([^"]+)"',
            html,
            re.IGNORECASE,
        )
        canonical_url = canonical_match.group(1).rstrip("/") if canonical_match else ""
        if not (
            isinstance(embedded_user, str) and embedded_user.lower() == user.lower()
        ) and canonical_url.lower() != url.lower():
            return Result.error("Linktree profile markers were missing")

        extra = {}
        media = {}

        name = page_props.get("pageTitle") or account.get("pageTitle")
        if name:
            extra["name"] = name.strip()

        description = page_props.get("description") or account.get("description")
        if description:
            extra["description"] = description.strip()

        avatar = account.get("profilePictureUrl") or page_props.get("customAvatar")
        if avatar:
            media["avatar"] = avatar.strip()

        verified = page_props.get("isProfileVerified")
        if verified is not None:
            extra["verified"] = verified

        links = page_props.get("links", [])
        if links:
            extra["showcased_links"] = [
                f"{link.get('title', '').strip()}: {link.get('url', '').strip()}"
                for link in links
                if link.get("url")
            ]

        social_links = page_props.get("socialLinks", [])
        if social_links:
            extra["social_links"] = [
                f"{link.get('platform', '').strip()}: {link.get('url', '').strip()}"
                for link in social_links
                if link.get("url")
            ]

        # Fallback to metadata regex if NEXT_DATA parsing failed or was incomplete
        if not page_props:
            title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE)
            if title:
                extra["name"] = title.group(1).split("| Linktree")[0].strip()

            description = re.search(
                r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"',
                html,
                re.IGNORECASE,
            )
            if description:
                extra["description"] = description.group(1).strip()

            image = re.search(
                r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
                html,
                re.IGNORECASE,
            )
            if image:
                media["avatar"] = image.group(1).strip()

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)
