import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result

BASE_URL = "https://www.pornhub.com"
SHOW_URL = "https://pornhub.com"
CHECK_API = f"{BASE_URL}/api/v1/user/create_account_check"

# The token is only reachable through the create_account_check URL Pornhub
# embeds (HTML-escaped) in the page's signup config.
TOKEN_RE = re.compile(r"create_account_check\?token=([A-Za-z0-9_.\-]+)")

# Pornhub no longer discloses registration for the address as typed: a
# deliverable address always gets the same "if this email is already
# registered" placeholder, and that path is what mails the account holder.
# Probing a sub-addressed alias sidesteps both problems, because Pornhub
# normalises the "+tag" away and then answers plainly.
PROBE_TAG = "+phck"

HEADERS = {
    "x-requested-with": "XMLHttpRequest",
    "origin": BASE_URL,
    "referer": BASE_URL + "/",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
}


async def _check(email: str) -> Result:
    local, _, domain = email.rpartition("@")
    if not local or not domain:
        return Result.error("Not a valid email address")

    if "+" in local:
        return Result.error(
            "Address is already sub-addressed; Pornhub cannot be probed for it"
        )

    try:
        landing = await impersonate_request_async(BASE_URL + "/", allow_redirects=True)
        token_match = TOKEN_RE.search(landing.text)

        if not token_match:
            return Result.error("Failed to extract dynamic token from HTML")

        response = await impersonate_request_async(
            CHECK_API,
            "POST",
            params={"token": token_match.group(1)},
            headers=HEADERS,
            data={"check_what": "email", "email": f"{local}{PROBE_TAG}@{domain}"},
        )

        if response.status_code == 429:
            return Result.error("Rate limited, wait for a few minutes")

        if response.status_code != 200:
            return Result.error(f"HTTP Error: {response.status_code}")

        data = response.json()
        status = data.get("email")
        error_msg = data.get("error_message", "")

        if status == "create_account_passed":
            return Result.available(url=SHOW_URL)

        if "has been taken" in error_msg:
            return Result.taken(url=SHOW_URL)

        if "delivery issues" in error_msg:
            return Result.error(url=SHOW_URL, reason="The email is experiencing email delivery issues")

        # Pornhub refuses to check some providers at all (proton.me, zoho.com),
        # which is a rule about the domain rather than a verdict on the address.
        if "is not allowed" in error_msg:
            return Result.error(
                url=SHOW_URL,
                reason=f"Pornhub does not accept registrations from '{domain}'",
            )

        # Sub-addressing is only accepted for mailboxes that actually resolve,
        # so an unusable alias says nothing about the address it derives from.
        if "invalid or cannot be used" in error_msg:
            return Result.error(
                url=SHOW_URL,
                reason=f"Domain '{domain}' does not support the sub-address probe",
            )

        return Result.error(f"Unexpected API response: {status}: {error_msg}")

    except Exception as e:
        return Result.error(e)


async def validate_pornhub(email: str) -> Result:
    return await _check(email)
