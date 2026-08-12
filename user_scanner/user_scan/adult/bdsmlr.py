import json

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

# bdsmlr.com is a client-rendered SPA: every /blog/<name> URL serves the same
# empty shell, so only this backend call distinguishes a real blog. It is
# POST-only — a GET answers 404 regardless of the handle.
API_URL = "https://api-prod.bdsmlr.com/v2/api/get-blog"

EMPTY_DESCRIPTIONS = ("", "no description")


def validate_bdsmlr(user):
    show_url = f"https://bdsmlr.com/blog/{user}"

    def process(response):
        try:
            data = response.json()
        except ValueError:
            return Result.error(f"Unexpected response body (HTTP {response.status_code})", url=show_url)

        error = data.get("error")

        blog = data.get("blog")
        if isinstance(blog, dict) and blog.get("name"):
            return Result.taken(extra=_extra(blog), media=_media(blog), url=show_url)

        if error == "blog not found":
            return Result.available(url=show_url)

        # "blog gone" is a deleted blog: the name is neither free nor backed by
        # a profile, so it must not become a verdict.
        return Result.error(error or f"Unexpected response body (HTTP {response.status_code})", url=show_url)

    return generic_validate(
        API_URL,
        process,
        show_url=show_url,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        content=json.dumps({"blog_name": user}),
    )


def _extra(blog: dict) -> dict:
    # A renamed blog still resolves under its old handle, so the canonical name
    # is reported to make that visible rather than silently labelling the
    # requested handle with another blog's metadata.
    extra = {
        "username": blog.get("name"),
        "blog_id": blog.get("id"),
        "owner_user_id": blog.get("ownerUserId"),
        "fullname": blog.get("title"),
        "posts": blog.get("postsCount"),
        "followers": blog.get("followersCount"),
    }

    description = blog.get("description") or ""
    if description.strip().lower() not in EMPTY_DESCRIPTIONS:
        extra["bio"] = description

    labels = (blog.get("personals") or {}).get("labels")
    if labels:
        extra["personals"] = ", ".join(sorted(labels))

    return extra


def _media(blog: dict) -> dict:
    # Both URLs are signed and expire; they are reported as-is.
    return {"avatar": blog.get("avatarUrl") or "", "cover": blog.get("coverUrl") or ""}
