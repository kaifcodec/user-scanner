import re
import json
import html

from user_scanner.core.orchestrator import generic_validate, Result


def validate_xvideos(user):
    url = f"https://www.xvideos.com/profiles/{user}"
    show_url = url

    def process(response):
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code != 200:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

        # A real profile is titled "<name> - Profile page - XVIDEOS.COM"; a
        # missing handle 404s with an "Unknown profile" page.
        if "profile page" in _title(response.text).lower():
            return Result.taken(extra=_extract_profile(response.text), url=show_url)

        return Result.error("Profile confirmation not found", url=show_url)

    return generic_validate(url, process, show_url=show_url)


def _extract_profile(html_text: str) -> dict:
    extra = {}

    # Structured identity from the embedded JSON `user` object.
    user = _user_object(html_text)
    if user.get("display"):
        extra["name"] = user["display"]
    if user.get("id_user"):
        extra["user_id"] = str(user["id_user"])
    avatar = user.get("profile_picture") or user.get("profile_picture_small")
    if avatar:
        extra["avatar"] = avatar

    # The visible "profile info" panel carries gender, age, country, hits,
    # languages, signup, last activity, plus any personal/physical details the
    # user filled in. Each row is:
    #   <p id="pinfo-<field>"><strong>Label:</strong><span>Value</span></p>
    for row in re.finditer(
        r'<p id="pinfo-[a-z-]+"[^>]*>\s*<strong>\s*(.*?):?\s*</strong>\s*<span>(.*?)</span>',
        html_text, re.DOTALL):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", row.group(1))).strip()
        value = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", row.group(2))).strip())
        # "Display" is the toggle link on the collapsible personal/physical rows.
        if label and value and value.lower() != "display":
            extra[label] = value

    return extra


def _user_object(html_text: str) -> dict:
    # The page embeds the profile as a JSON `user` object whose `url` field comes
    # last, so match up to it and parse the whole object.
    match = re.search(r'"user":(\{.*?"url":"[^"]*"\})', html_text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def _title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1)).strip() if match else ""
