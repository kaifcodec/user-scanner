import html
import json
import re
from urllib.parse import quote, urlsplit

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

HEADERS = {"User-Agent": "Twitterbot/1.0"}

ABOUT_KEYS = {
    "industry": "industry",
    "size": "company_size",
    "organizationType": "organization_type",
    "foundedOn": "founded",
    "specialties": "specialties",
}
ABOUT_RE = re.compile(
    rf'data-test-id="about-us__({"|".join(ABOUT_KEYS)})"[^>]*>.*?<dd[^>]*>(.*?)</dd>',
    re.DOTALL,
)


def _ld_nodes(text: str):
    for block in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL
    ):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        yield from data.get("@graph", [data])


def _clean_html(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _og(text: str, prop: str) -> str | None:
    match = re.search(
        rf'<meta[^>]+property="{re.escape(prop)}"[^>]+content="([^"]*)"', text
    )
    return html.unescape(match.group(1)) if match else None


def _latest_published(nodes: list[dict]) -> str | None:
    dates = [
        node["datePublished"]
        for node in nodes
        if node.get("@type") in ("Article", "DiscussionForumPosting")
        and node.get("datePublished")
    ]
    return max(dates)[:10] if dates else None


def validate_linkedin_company(user: str) -> Result:
    url = f"https://www.linkedin.com/company/{quote(user, safe='')}"

    def process(response: httpx.Response) -> Result:
        text = response.text
        if response.status_code == 404 and "<title>LinkedIn</title>" in text:
            return Result.available()
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        nodes = list(_ld_nodes(text))
        organization = next(
            (node for node in nodes if node.get("@type") == "Organization"),
            None,
        )
        canonical = organization.get("url") if organization else None
        canonical_path = urlsplit(canonical).path if canonical else ""
        if not organization or not canonical_path.startswith("/company/"):
            return Result.error("LinkedIn company profile markers were missing")

        address = organization.get("address") or {}
        employees = organization.get("numberOfEmployees") or {}
        followers = re.search(
            r"([\d,]+) followers on LinkedIn", _og(text, "og:description") or ""
        )
        logo = organization.get("logo") or {}
        canonical_handle = canonical_path.rstrip("/").rsplit("/", 1)[-1]
        about = {
            ABOUT_KEYS[key]: _clean_html(value)
            for key, value in ABOUT_RE.findall(text)
        }

        return Result.taken(
            extra={
                "name": organization.get("name"),
                "description": _clean_html(organization.get("description")),
                "slogan": organization.get("slogan"),
                "website": organization.get("sameAs"),
                "city": address.get("addressLocality"),
                "region": address.get("addressRegion"),
                "country": address.get("addressCountry"),
                "employees": employees.get("value"),
                "followers": followers.group(1) if followers else None,
                "last_posted": _latest_published(nodes),
                **about,
                "canonical_handle": (
                    canonical_handle
                    if canonical_handle.casefold() != user.casefold()
                    else None
                ),
            },
            media={"logo": logo.get("contentUrl") or _og(text, "og:image")},
        )

    return generic_validate(
        url, process, show_url=f"{url}/", headers=HEADERS, follow_redirects=True
    )
