import re
from urllib.parse import quote

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

SHOW_URL = "https://github.com"
SEARCH_API = "https://api.github.com/search/users"
SIGNUP_URL = "https://github.com/signup"
VALIDITY_URL = "https://github.com/email_validity_checks"

# The signup form carries one CSRF token per auto-check endpoint and emits the
# value before the data-csrf marker, so the token has to be taken from inside
# the email_validity_checks block rather than from the first match on the page.
CSRF_RE = re.compile(
    r'<auto-check[^>]*src="/email_validity_checks"'
    r'[\s\S]*?<input[^>]*value="([^"]+)"[^>]*data-csrf="true"'
)


async def _check(email: str) -> Result:
    # The search API confirms a hit outright and costs one request, so it runs
    # before the signup probe. It only sees accounts that publish the address
    # on their profile, so a miss still has to fall through.
    found = await _search_public_profiles(email)
    if found is not None:
        return found

    return await _check_signup_availability(email)


async def _search_public_profiles(email: str) -> Result | None:
    try:
        response = await impersonate_request_async(
            f"{SEARCH_API}?q={quote(email)}+in:email",
            headers={"accept": "application/vnd.github+json"},
        )
    except Exception:
        return None

    if response.status_code != 200:
        return None

    items = response.json().get("items") or []
    if not items:
        return None

    user = items[0]
    return Result.taken(
        url=SHOW_URL,
        extra={
            "login": user.get("login"),
            "user_id": user.get("id"),
            "profile": user.get("html_url"),
            "account_type": user.get("type"),
            "matched_by": "public profile email",
        },
        media={"avatar": user.get("avatar_url")},
    )


async def _check_signup_availability(email: str) -> Result:
    try:
        signup = await impersonate_request_async(SIGNUP_URL, allow_redirects=True)
        csrf_match = CSRF_RE.search(signup.text)

        if not csrf_match:
            # GitHub fronts /signup with DataDome, whose interstitial no HTTP
            # client can clear; the address may still be registered privately.
            return Result.error(
                "GitHub's signup form is behind a bot challenge, and the address "
                "is not on any public profile"
            )

        response = await impersonate_request_async(
            VALIDITY_URL,
            "POST",
            data={"authenticity_token": csrf_match.group(1), "value": email},
            headers={
                "origin": SHOW_URL,
                "referer": SIGNUP_URL,
                "accept": "*/*",
            },
        )
        body = response.text

        if "already associated with an account" in body:
            return Result.taken(url=SHOW_URL)

        if response.status_code == 200 and "Email is available" in body:
            return Result.available(url=SHOW_URL)

        return Result.error(
            f"Unexpected status code: {response.status_code}, report this via GitHub issues"
        )

    except Exception as e:
        return Result.error(f"unexpected exception: {e}")


async def validate_github(email: str) -> Result:
    return await _check(email)
