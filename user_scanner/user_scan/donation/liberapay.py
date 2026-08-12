from user_scanner.core.orchestrator import generic_validate, make_request, Result
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
            media = {}
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            if title_match:
                name = title_match.group(1).split("&#39;s profile")[0].split("'s profile")[0].strip()
                if name.lower() != user.lower():
                    extra["name"] = name
            accounts = _verified_accounts(response.text)
            if accounts:
                extra["verified_accounts"] = ", ".join(accounts)

            # Enrich profile metadata via public.json API
            try:
                json_url = f"https://liberapay.com/{user}/public.json"
                json_headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
                json_resp = make_request(json_url, headers=json_headers)
                if json_resp.status_code == 200:
                    data = json_resp.json()
                    if data.get("avatar"):
                        media["avatar"] = data["avatar"]
                    if data.get("display_name"):
                        extra["name"] = data["display_name"]
                    if data.get("id"):
                        extra["id"] = data["id"]
                    if data.get("kind"):
                        extra["kind"] = data["kind"]
                    if data.get("npatrons"):
                        extra["patrons"] = data["npatrons"]
                    if isinstance(data.get("receiving"), dict):
                        amt = data["receiving"].get("amount")
                        curr = data["receiving"].get("currency", "EUR")
                        if amt:
                            extra["receiving"] = f"{amt} {curr}"
                    if isinstance(data.get("giving"), dict):
                        amt = data["giving"].get("amount")
                        curr = data["giving"].get("currency", "EUR")
                        if amt and amt != "0.00":
                            extra["giving"] = f"{amt} {curr}"
                    if data.get("summaries") and isinstance(data["summaries"], list):
                        summaries = data["summaries"]
                        en_summary = next(
                            (s.get("content") for s in summaries if isinstance(s, dict) and s.get("lang") == "en"),
                            None
                        )
                        if not en_summary and summaries and isinstance(summaries[0], dict):
                            en_summary = summaries[0].get("content")
                        if en_summary:
                            extra["summary"] = en_summary
            except Exception:
                pass

            return Result.taken(extra=extra, media=media)
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
