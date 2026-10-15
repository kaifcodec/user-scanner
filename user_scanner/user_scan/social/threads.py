from html import unescape
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_threads(user: str) -> Result:
    if not (1 <= len(user) <= 30):
        return Result.error("Length must be between 1 and 30 characters")

    if not re.fullmatch(r"[A-Za-z0-9._]+", user):
        return Result.error("Threads usernames can only use letters, numbers, underscores, and periods")

    url = f"https://www.threads.net/@{user}"

    def process(response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        og_title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', response.text)
        title_tag_match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE)
        title_text = unescape(
            og_title_match.group(1) if og_title_match else (title_tag_match.group(1) if title_tag_match else "")
        ).strip()

        # Non-existent handles render the Threads login landing page
        if any(marker in title_text for marker in ("Threads • Log in", "Threads \u2022 Log in", "Log in \u2022 Threads")):
            return Result.available()

        if f"@{user.lower()}" in title_text.lower():
            extra, media = _extract_threads(response.text, user)
            return Result.taken(extra=extra, media=media)

        return Result.error("Unexpected response title format")

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)


def _extract_threads(html: str, user: str) -> tuple[dict, dict]:
    extra: dict[str, str] = {}
    media: dict[str, str] = {}

    og_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
    if og_title:
        title_text = unescape(og_title.group(1)).strip()
        m = re.search(r"^(.*?)\s*\(@([A-Za-z0-9._]+)\)", title_text)
        if m:
            name = m.group(1).strip()
            if name and name.lower() != user.lower():
                extra["name"] = name

    og_desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"', html)
    if og_desc:
        desc_text = unescape(og_desc.group(1)).strip()
        desc_text = re.sub(
            r"\s*See the latest conversations with\s+@[A-Za-z0-9._]+\.?\s*$", "", desc_text, flags=re.IGNORECASE
        ).strip()
        parts = [p.strip() for p in desc_text.split(" • ") if p.strip()]
        bio_parts = []
        for part in parts:
            if re.search(r"^\d+[\d.,]*[KMkm]?\s+Followers?$", part, re.IGNORECASE):
                extra["followers"] = part.split()[0]
            elif re.search(r"^\d+[\d.,]*[KMkm]?\s+Threads?$", part, re.IGNORECASE):
                extra["threads"] = part.split()[0]
            else:
                bio_parts.append(part)
        if bio_parts:
            extra["bio"] = " • ".join(bio_parts)

    og_img = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"', html)
    if og_img:
        img_url = unescape(og_img.group(1)).strip()
        if img_url and not any(k in img_url for k in ("rsrc.php", "kHwIMM5b8PW")):
            media["avatar"] = img_url

    return extra, media
