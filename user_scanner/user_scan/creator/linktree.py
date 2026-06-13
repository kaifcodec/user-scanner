import re
import json
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_linktree(user):
    url = f"https://linktr.ee/{user}"
    show_url = f"https://linktr.ee/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            html = response.text
            extra = {}

            # Try to parse __NEXT_DATA__ first for deep extraction
            next_data_match = re.search(
                r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            parsed_successfully = False
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    page_props = data.get('props', {}).get('pageProps', {})
                    account = page_props.get('account', {})

                    name = page_props.get(
                        'pageTitle') or account.get('pageTitle')
                    if name:
                        extra['name'] = name.strip()

                    desc = page_props.get(
                        'description') or account.get('description')
                    if desc:
                        extra['description'] = desc.strip()

                    avatar = account.get(
                        'profilePictureUrl') or page_props.get('customAvatar')
                    if avatar:
                        extra['avatar'] = avatar.strip()

                    verified = page_props.get('isProfileVerified')
                    if verified is not None:
                        extra['verified'] = verified

                    links = page_props.get('links', [])
                    if links:
                        extra['showcased_links'] = [
                            f"{link.get('title', '').strip()}: {link.get('url', '').strip()}"
                            for link in links if link.get('url')
                        ]

                    social = page_props.get('socialLinks', [])
                    if social:
                        extra['social_links'] = [
                            f"{s.get('platform', '').strip()}: {s.get('url', '').strip()}"
                            for s in social if s.get('url')
                        ]
                    parsed_successfully = True
                except Exception:
                    pass

            # Fallback to metadata regex if NEXT_DATA parsing failed or was incomplete
            if not parsed_successfully:
                title = re.search(
                    r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
                if title:
                    title_text = title.group(1).strip()
                    if " | Linktree" in title_text:
                        title_text = title_text.split(" | Linktree")[0]
                    elif "| Linktree" in title_text:
                        title_text = title_text.split("| Linktree")[0]
                    extra["name"] = title_text.strip()

                desc = re.search(
                    r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html, re.IGNORECASE)
                if desc:
                    extra["description"] = desc.group(1).strip()

                img = re.search(
                    r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html, re.IGNORECASE)
                if img:
                    extra["image"] = img.group(1).strip()

            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)
