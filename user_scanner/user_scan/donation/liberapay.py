from user_scanner.core.orchestrator import generic_validate, Result
import html
import re

# Liberapay connects an "elsewhere" account through OAuth only, so the block the
# profile renders is the site vouching for ownership rather than free text the
# owner typed. /<user>/public.json omits it, leaving the page as the only source.
ACCOUNTS_MARKER = "owns the following accounts on other platforms"
ACCOUNTS_BLOCK_OPEN = '<div class="accounts">'
DIV_TAG_RE = re.compile(r"</?div\b", re.I)
ACCOUNT_ANCHOR_RE = re.compile(r'<a\b([^>]*\bclass="account-link"[^>]*)>(.*?)</a>', re.S)
HREF_RE = re.compile(r'href="([^"]+)"')
PLATFORM_RE = re.compile(r'<span class="sr-only">\s*([^<:]+?)\s*:?\s*</span>')


def validate_liberapay(user):
    url = f"https://en.liberapay.com/{user}"
    show_url = f"https://en.liberapay.com/{user}"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-Us,pt;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
    }

    def process(response):
        if response.status_code == 200:
            extra = {}
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                name = title_match.group(1).split("&#39;s profile")[0].split("'s profile")[0].strip()
                if name.lower() != user.lower():
                    extra["name"] = name
            accounts = _verified_accounts(response.text)
            if accounts:
                extra["verified_accounts"] = ", ".join(accounts)
            return Result.taken(extra=extra)
        elif response.status_code in (404, 410):
            return Result.available()
        return Result.error(f"Unexpected status {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers, follow_redirects=True)


def _verified_accounts(page):
    accounts = []
    seen = set()
    for match in ACCOUNT_ANCHOR_RE.finditer(_accounts_block(page)):
        href = HREF_RE.search(match.group(1))
        if not href:
            continue
        # Mastodon renders the visible name as user@instance, so the href is the
        # only place a usable profile URL appears.
        url = html.unescape(href.group(1)).strip()
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        platform = PLATFORM_RE.search(match.group(2))
        label = html.unescape(platform.group(1)).strip() if platform else "Account"
        accounts.append(f"{label}: {url}")
    return accounts


def _accounts_block(page):
    """The linked-accounts markup only, empty when the profile lists none.

    The rest of the page renders donation relationships and patron lists naming
    other people, so a document-wide sweep would harvest strangers.
    """
    marker = page.find(ACCOUNTS_MARKER)
    if marker < 0:
        return ""
    start = page.find(ACCOUNTS_BLOCK_OPEN, marker)
    if start < 0:
        return ""
    depth = 0
    for tag in DIV_TAG_RE.finditer(page, start):
        depth += -1 if tag.group(0).startswith("</") else 1
        if depth == 0:
            return page[start : tag.start()]
    return ""
