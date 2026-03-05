import httpx
import re
from html import unescape
from user_scanner.core.result import Result


def _extract_form_fields(html: str) -> dict:
    fields = {}
    for tag in re.finditer(r"<input\s[^>]*>", html, re.IGNORECASE):
        tag_str = tag.group(0)
        name = re.search(r'name=["\']([^"\']*)["\']', tag_str)
        value = re.search(r'value=["\']([^"\']*)["\']', tag_str)
        if name and value:
            fields[name.group(1)] = value.group(1)
    return fields


def _is_captcha(html: str) -> bool:
    lower = html.lower()
    return any(
        marker in lower
        for marker in ("captcha", "type the characters", "robot check", "opf-captcha")
    )


def _extract_form_action(html: str) -> str | None:
    """Two-pass: find the signIn or claim form regardless of attribute order."""
    for form_tag in re.finditer(r"<form\s[^>]*>", html, re.IGNORECASE):
        tag = form_tag.group(0)
        action_match = re.search(r'action=["\']([^"\']*)["\']', tag)
        if not action_match:
            continue
        action = unescape(action_match.group(1))
        name_match = re.search(r'name=["\']([^"\']*)["\']', tag)
        if name_match and name_match.group(1) == "signIn":
            return action
        if "/ap/signin" in action or "/ax/claim" in action:
            return action
    return None


async def _check(email: str) -> Result:
    """
    Probe Amazon's sign-in flow to check if an email is registered.

    Amazon A/B tests between /ap/signin and /ax/claim pages; both are handled.
    Rate limits: may block after repeated requests from the same IP.
    """
    show_url = "https://www.amazon.com"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    signin_url = (
        "https://www.amazon.com/ap/signin?"
        "openid.pape.max_auth_age=0"
        "&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F"
        "%3F_encoding%3DUTF8%26ref_%3Dnav_ya_signin"
        "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        "&openid.assoc_handle=usflex"
        "&openid.mode=checkid_setup"
        "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
    )

    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, headers=headers
        ) as client:
            # 1. Load the sign-in page and extract form fields + action URL
            resp = await client.get(signin_url)

            if resp.status_code != 200:
                return Result.error(
                    f"Failed to load sign-in page: HTTP {resp.status_code}",
                    url=show_url,
                )

            if _is_captcha(resp.text):
                return Result.error(
                    "CAPTCHA detected (IP may be flagged)", url=show_url
                )

            data = _extract_form_fields(resp.text)
            if not data:
                return Result.error(
                    "Could not extract form fields", url=show_url
                )

            data["email"] = email

            post_url = _extract_form_action(resp.text)
            if not post_url:
                return Result.error(
                    "Could not find sign-in form action URL", url=show_url
                )
            if post_url.startswith("/"):
                post_url = "https://www.amazon.com" + post_url

            # 2. Submit the email
            resp = await client.post(post_url, data=data)

            if resp.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if resp.status_code not in (200, 302):
                return Result.error(
                    f"Unexpected HTTP {resp.status_code}", url=show_url
                )

            if _is_captcha(resp.text):
                return Result.error(
                    "CAPTCHA triggered (IP may be flagged)", url=show_url
                )

            # 3. If Amazon asks for a password, the email is registered
            if 'id="auth-password-missing-alert"' in resp.text:
                return Result.taken(url=show_url)

            return Result.available(url=show_url)

    except httpx.TimeoutException:
        return Result.error("Connection timed out", url=show_url)
    except Exception as e:
        return Result.error(str(e), url=show_url)


async def validate_amazon(email: str) -> Result:
    return await _check(email)
