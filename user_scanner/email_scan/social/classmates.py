import re

from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://www.classmates.com"
    login_url = "https://www.classmates.com/auth/login"

    # No User-Agent or client hints: the impersonating transport supplies a set
    # that matches its TLS fingerprint, and overriding half of it re-trips the WAF.
    headers = {
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Origin': "https://www.classmates.com",
        'Referer': login_url,
        'Accept-Language': "en-US,en;q=0.9"
    }

    try:
        # The login page is fetched as a plain navigation; sending the form's
        # Origin/Referer on it is what the WAF answers 403 to.
        r_init = await impersonate_request_async(login_url, allow_redirects=True)

        if r_init.status_code == 403:
            return Result.error("Caught by WAF (403) during Handshake")

        csrf_match = re.search(r'name="_csrf" value="([^"]+)"', r_init.text)
        if not csrf_match:
            return Result.error("Failed to extract CSRF token from login page")

        payload = {
            '_csrf': csrf_match.group(1),
            'successUrl': "",
            'emailOrRegId': email,
            'password': "SafetyMismatch_123!",
            'rememberme': "no"
        }

        response = await impersonate_request_async(
            login_url, "POST", data=payload, headers=headers, allow_redirects=True
        )

        if response.status_code == 403:
            return Result.error("Caught by WAF or IP Block (403) during Check")

        if response.status_code == 429:
            return Result.error("Rate limited by Classmates (429)")

        res_text = response.text

        if "invalid registration/password" in res_text:
            return Result.taken(url=show_url)

        if "did not find an account for the email address" in res_text:
            return Result.available(url=show_url)

        return Result.error("Unexpected response body structure")

    except Exception as e:
        return Result.error(e)


async def validate_classmates(email: str) -> Result:
    return await _check(email)
