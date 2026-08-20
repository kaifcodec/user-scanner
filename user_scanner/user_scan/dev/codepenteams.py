import html
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result


PROFILE_QUERY = """
query ProfileOwner($ownerUsername: String!, $ownerType: OwnerEnum!) {
  ownerByUsername(ownerUsername: $ownerUsername, ownerType: $ownerType) {
    id
    title
    avatar512
    pro
    urls
    location
    bio
    verified
    counts {
      id
      followers
      following
      pens
      posts
      collections
    }
  }
}
"""


def _meta(document: str, name: str) -> str:
    match = re.search(
        rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+'
        r'content=(["\'])(.*?)\1',
        document,
        re.IGNORECASE | re.DOTALL,
    )
    return html.unescape(match.group(2).strip()) if match else ""


def _enrichment(
    user: str, document: str, profile_url: str
) -> tuple[dict[str, str | bool | int | list[str] | None], dict[str, str]]:
    extra: dict[str, str | bool | int | list[str] | None] = {}
    csrf_token = _meta(document, "csrf-token")
    if not csrf_token:
        return extra, {}

    try:
        response = make_request(
            "https://codepen.io/graphql",
            method="POST",
            headers={"referer": profile_url, "x-csrf-token": csrf_token},
            json={
                "query": PROFILE_QUERY,
                "variables": {
                    "ownerType": "Team",
                    "ownerUsername": user,
                },
            },
        )
        profile = response.json()["data"]["ownerByUsername"]
        if not isinstance(profile, dict):
            return extra, {}
    except Exception:
        return extra, {}

    counts = profile.get("counts") or {}
    extra["hashid"] = profile.get("id")
    for field in ("id", "followers", "following", "pens", "posts", "collections"):
        extra[field] = counts.get(field)
    for field in ("pro", "verified"):
        extra[field] = profile.get(field)
    if links := [url for url in profile.get("urls") or [] if url]:
        extra["links"] = list(dict.fromkeys(links))
    extra["location"] = str(profile.get("location") or "").strip()
    extra["fullname"] = str(profile.get("title") or "").strip()
    extra["bio"] = html.unescape(str(profile.get("bio") or "")).strip()
    return extra, {"avatar": str(profile.get("avatar512") or "")}


def validate_codepenteams(user: str) -> Result:
    encoded = quote(user, safe="")
    url = f"https://codepen.io/team/{encoded}"

    def process(response):
        document = response.text
        if response.status_code == 404 and 'data-test-id="text-404"' in document:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        canonical = _meta(document, "og:url")
        if canonical.rstrip("/").casefold() != url.casefold():
            return Result.error("Profile response did not match the requested username")

        extra, media = _enrichment(user, document, url)
        return Result.taken(extra=extra, media=media)

    return generic_validate(url, process, show_url=url, follow_redirects=True)
