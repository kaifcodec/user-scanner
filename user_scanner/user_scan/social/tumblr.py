import json
import re

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BLOG_MARKER = '"blog":'
NOT_FOUND_TITLE_RE = re.compile(r"<title[^>]*>\s*Not found\.", re.IGNORECASE)


def validate_tumblr(user: str) -> Result:
    if not re.fullmatch(r"[A-Za-z0-9-]{1,32}", user):
        return Result.error("Only letters, numbers and hyphens allowed (max 32)")

    # Blog names are always lowercase and the www route is case-sensitive, so an
    # unnormalised handle 404s on a name that is in fact taken.
    user = user.lower()
    show_url = f"https://www.tumblr.com/{user}"

    def process(response) -> Result:
        if response.status_code == 404 and NOT_FOUND_TITLE_RE.search(response.text):
            return Result.available()

        location = response.headers.get("location", "")
        if response.status_code == 302 and f"/login_required/{user}" in location:
            return Result.taken(extra={"username": user, "visibility": "login required"})

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}")

        blog = _find_blog(response.text, user)
        if not blog:
            return Result.error("Unrecognised profile payload")

        extra = {"username": blog["name"]}
        if title := blog.get("title"):
            extra["title"] = title
        if description := _npf_text(blog.get("descriptionNpf")):
            extra["description"] = description
        if uuid := blog.get("uuid"):
            extra["uuid"] = uuid
        if (url := blog.get("url")) and url != show_url:
            extra["blog_url"] = url
        if tags := _top_tags(blog.get("topTags")):
            extra["top_tags"] = tags
        if blog.get("isAdult"):
            extra["adult"] = "true"
        if blog.get("isPasswordProtected"):
            extra["password_protected"] = "true"
        if blog.get("ask"):
            extra["asks_enabled"] = "true"

        media = {}
        if avatar := _largest_avatar(blog.get("avatar")):
            media["avatar"] = avatar
        if header := (blog.get("theme") or {}).get("headerImage"):
            media["header"] = header

        return Result.taken(extra=extra, media=media)

    # The <user>.tumblr.com host answers every request with Tumblr's own
    # "Checking your browser..." interstitial, which no HTTP client clears;
    # the www route serves the blog payload directly. Redirects must stay
    # unfollowed: the hop to /login_required/<user> is the only signal that
    # separates a login-walled blog from a free name.
    return impersonate_validate(
        show_url, process, show_url=show_url, allow_redirects=False
    )


def _find_blog(html: str, user: str) -> dict | None:
    """Return the embedded blog object whose name matches ``user``.

    The page carries sibling blog objects for recommendation rails, so the
    first match is not necessarily the requested one.
    """
    decoder = json.JSONDecoder()
    index = html.find(BLOG_MARKER)
    while index != -1:
        try:
            blog, _ = decoder.raw_decode(html, index + len(BLOG_MARKER))
        except ValueError:
            blog = None
        if isinstance(blog, dict) and blog.get("name", "").lower() == user.lower():
            return blog
        index = html.find(BLOG_MARKER, index + len(BLOG_MARKER))
    return None


def _npf_text(blocks) -> str:
    if not isinstance(blocks, list):
        return ""
    texts = [
        block["text"]
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
    ]
    return "\n".join(texts).strip()


def _top_tags(tags) -> str:
    if not isinstance(tags, list):
        return ""
    return ", ".join(tag["tag"] for tag in tags if isinstance(tag, dict) and tag.get("tag"))


def _largest_avatar(avatars) -> str:
    if not isinstance(avatars, list):
        return ""
    sized = [a for a in avatars if isinstance(a, dict) and a.get("url")]
    if not sized:
        return ""
    return max(sized, key=lambda a: a.get("width") or 0)["url"]
