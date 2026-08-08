import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

PROFILE_TITLE_RE = re.compile(r"<title>([^<]+?)(?:&#x27;s|&#39;s|'s) profile")


def validate_producthunt(user: str) -> Result:
    if not (2 <= len(user) <= 32):
        return Result.error("Length must be 2-32 characters.")

    # Rules: Letters, numbers, and underscores only.
    if not re.match(r"^[a-zA-Z0-9_]+$", user):
        return Result.error("Only use letters, numbers, and underscores.")

    url = f"https://www.producthunt.com/@{user}"

    def process(response):
        # Cloudflare serves a managed challenge on every path of this domain in
        # some regions; no HTTP client can clear it, so never call it a verdict.
        if response.headers.get("cf-mitigated") == "challenge":
            return Result.error("Cloudflare challenge, cannot be solved without a browser")

        if response.status_code == 404:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        # A profile page is confirmed by the possessive title Product Hunt
        # renders server-side; nothing else under /@ carries it, so a 200
        # without it is an interstitial rather than a hit.
        if not PROFILE_TITLE_RE.search(response.text):
            return Result.error("200 without a profile title, cannot confirm the handle")

        return Result.taken(extra=_extract(response.text))

    return impersonate_validate(url, process, show_url=url, allow_redirects=True)


def _extract(body: str) -> dict:
    extra = {}

    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    if ld:
        try:
            data = json.loads(ld.group(1))
            if isinstance(data, list):
                data = data[0]
            if name := data.get("name"):
                extra["name"] = name
            if profile_url := data.get("url"):
                extra["url"] = profile_url
        except (json.JSONDecodeError, AttributeError, IndexError, KeyError):
            pass

    if "name" in extra:
        return extra

    title = PROFILE_TITLE_RE.search(body)
    if title:
        extra["name"] = title.group(1).strip()
        return extra

    meta = re.search(r"See what kind of products\s+([^\(]+)", body)
    if meta:
        extra["name"] = meta.group(1).strip()

    return extra
