import base64
import json
import re
from html import unescape
from typing import Any, Dict, Tuple

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def _flag_to_country_code(flag: str) -> str:
    """Convert Unicode regional indicator flag emoji to 2-letter country code (e.g. 🇺🇸 -> US)."""
    return "".join(chr(ord(c) - 0x1F1E6 + ord("A")) for c in flag)


def _extract_peerpush_data(html: str, user: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Extract profile metadata (bio, name, products, stats, links, badge) and media from PeerPush HTML."""
    extra: Dict[str, Any] = {}
    media: Dict[str, str] = {}

    # 1. Parse JSON-LD ProfilePage data
    ld_matches = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    for ld in ld_matches:
        if not ld.strip():
            continue
        try:
            data = json.loads(ld)
            if isinstance(data, dict) and data.get("@type") == "ProfilePage":
                main_entity = data.get("mainEntity", {})

                # Full name
                if name := main_entity.get("name"):
                    name_str = str(name).strip()
                    if name_str.lower() != user.lower():
                        extra["name"] = name_str

                # Direct image URL if available in JSON-LD
                if img_url := main_entity.get("image"):
                    if isinstance(img_url, str) and img_url.startswith("http"):
                        media["avatar"] = img_url

                # Creation date (ISO format YYYY-MM-DD)
                if date_created := data.get("dateCreated"):
                    date_str = str(date_created)
                    extra["joined"] = date_str.split("T")[0] if "T" in date_str else date_str

                # Products / Projects launched
                offers = main_entity.get("makesOffer", [])
                products = []
                for offer in offers:
                    if isinstance(offer, dict):
                        item = offer.get("itemOffered", {})
                        if isinstance(item, dict) and item.get("name"):
                            products.append(str(item["name"]))
                if products:
                    extra["products"] = ", ".join(products)
                    extra["products_count"] = len(products)

                # Interaction statistics
                stats = main_entity.get("interactionStatistic", [])
                for stat in stats:
                    if isinstance(stat, dict):
                        itype = (
                            str(stat.get("interactionType", {}).get("@id", ""))
                            .split("/")[-1]
                            .replace("Action", "")
                            .lower()
                        )
                        count = stat.get("userInteractionCount", 0)
                        if isinstance(count, int) and count > 0:
                            if itype == "like":
                                extra["upvotes_given"] = count
                            elif itype == "comment":
                                extra["comments"] = count
                            elif itype == "review":
                                extra["reviews"] = count
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    # 2. Parse HTML Profile Header
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if h1_match:
        h1_text = unescape(re.sub(r"<[^<]+?>", "", h1_match.group(1))).strip()

        # Country code from flag emoji in H1 (e.g. 🇺🇸 -> US, 🇪🇸 -> ES)
        flag_match = re.search(r"[\U0001F1E6-\U0001F1FF]{2}", h1_text)
        if flag_match:
            extra["country"] = _flag_to_country_code(flag_match.group(0))

    # Hero section container
    hero_match = re.search(
        r'<section[^>]*class=["\'][^"\']*hero-gradient[^"\']*["\'][^>]*>(.*?)</section>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if hero_match:
        hero_html = hero_match.group(1)

        # Avatar image URL (if not already extracted from JSON-LD)
        if "avatar" not in media:
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', hero_html, re.IGNORECASE)
            if img_match:
                avatar_url = img_match.group(1).strip()
                # PeerPush embeds the original CDN URL in a base64-encoded path
                b64_match = re.search(r"/([A-Za-z0-9+/=]{20,})\.(?:webp|png|jpe?g)", avatar_url)
                if b64_match:
                    try:
                        b64_str = b64_match.group(1)
                        b64_str += "=" * (-len(b64_str) % 4)
                        decoded = base64.b64decode(b64_str).decode("utf-8")
                        if decoded.startswith("http"):
                            avatar_url = decoded
                    except Exception:
                        pass
                if avatar_url.startswith("/"):
                    avatar_url = f"https://peerpush.com{avatar_url}"
                media["avatar"] = avatar_url

        # Bio / Tagline (the <p> right under the <h1> block)
        bio_match = re.search(
            r'<p[^>]*class=["\'][^"\']*text-neutral-600[^"\']*["\'][^>]*>(.*?)</p>',
            hero_html,
            re.DOTALL | re.IGNORECASE,
        )
        if bio_match:
            clean_bio = unescape(re.sub(r"<[^<]+?>", "", bio_match.group(1))).strip()
            if clean_bio:
                extra["bio"] = clean_bio

        # Badge (e.g. "3x Product of the Month", "2x Product of the Week", "Product of the Day")
        badge_match = re.search(
            r'<span[^>]*class=["\'][^"\']*bg-amber-50[^"\']*["\'][^>]*>(.*?)</span>',
            hero_html,
            re.DOTALL | re.IGNORECASE,
        )
        if badge_match:
            clean_badge = unescape(re.sub(r"<[^<]+?>", "", badge_match.group(1))).strip()
            if clean_badge:
                extra["badge"] = clean_badge

        # Fallback joined date if not present in JSON-LD
        if "joined" not in extra:
            joined_match = re.search(r"Joined\s+([A-Za-z]+\s+\d{4})", hero_html)
            if joined_match:
                extra["joined"] = joined_match.group(1).strip()

        # External Links (e.g. GitHub, LinkedIn, X, personal site)
        links = re.findall(r'<a[^>]+href=["\'](https?://[^"\']+)["\']', hero_html, re.IGNORECASE)
        external_links = [link for link in links if "peerpush.com" not in link]
        if external_links:
            extra["links"] = ", ".join(external_links)

    return extra, media


def validate_peerpush(user: str) -> Result:
    """Validate username availability on PeerPush (peerpush.com/u/<user>)."""
    if not (1 <= len(user) <= 50):
        return Result.error("Length must be 1-50 characters.")

    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", user):
        return Result.error("Invalid characters in username.")

    url = f"https://peerpush.com/u/{user}"
    show_url = f"https://peerpush.com/u/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response):
        # 1. Explicit verification of not-found state
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
        page_title = title_match.group(1).strip() if title_match else ""

        if (
            response.status_code == 404
            or "page not found" in page_title.lower()
            or "Page not found" in response.text
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of confirmed taken state
        if response.status_code == 200:
            if (
                f"@{user.lower()}" in page_title.lower()
                or "ProfilePage" in response.text
                or f"/u/{user.lower()}" in response.text.lower()
            ):
                extra, media = _extract_peerpush_data(response.text, user)
                return Result.taken(extra=extra, media=media, url=show_url)
            return Result.error("200 status without profile confirmation", url=show_url)

        # 3. Handle unexpected status codes
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
