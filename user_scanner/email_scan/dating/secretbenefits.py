import base64
import json
import random
import re
import string

import httpx

from user_scanner.core.result import Result

SIGN_PATTERN = re.compile(
    r"""
    \s*function\(x\)\s*\{\s*try\s*\{\s*return\s*\[
    '([^'\\]*)',\s*x\.codePointAt\(0\)\s*\*\s*x\.length\s*\^\s*(\d+),
    \s*\[\s*([0-3]\s*,\s*[0-3]\s*,\s*[0-3]\s*,\s*[0-3])\s*\]\.map\(function\(i\)\s*\{\s*return\s*\[
    '([^'\\]*)','([^'\\]*)','([^'\\]*)','([^'\\]*)'
    \]\[i\]\s*\}\)\.join\(''\),\s*'([^'\\]*)'
    \]\.join\('\ '\)\s*;?\s*\}\s*catch\s*\(e\)\s*\{
    \s*return\s*'error'\s*;?\s*\}\s*\}\s*
""",
    re.VERBOSE,
)


def _js_length(value: str) -> int:
    """Return the UTF-16 code unit count used by JavaScript string.length."""
    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def _codepoints(value: str) -> list[int]:
    """Return Unicode code points, combining explicit UTF-16 surrogate pairs."""
    normalized = value.encode("utf-16-le", errors="surrogatepass").decode(
        "utf-16-le", errors="surrogatepass"
    )
    return [ord(char) for char in normalized]


def _int32(value: int) -> int:
    """Wrap an integer to the signed 32-bit range used by JavaScript XOR."""
    return (value + 2**31) % 2**32 - 2**31


def _compute_signed3(email: str, source: str) -> str:
    """Reproduce the recognized sign_fn calculation without executing JavaScript.

    Raise ValueError if the source does not match the supported function format.
    """
    match = SIGN_PATTERN.fullmatch(source)
    if not match:
        raise ValueError("Unrecognized sign_fn format")
    prefix, mask, order, a, b, c, d, suffix = match.groups()
    fragments = (a, b, c, d)
    block = "".join(fragments[int(index.strip())] for index in order.split(","))
    points = _codepoints(email)
    product = points[0] * _js_length(email) if points else 0
    number = _int32(_int32(product) ^ _int32(int(mask)))
    return " ".join((prefix, str(number), block, suffix))


def _simulate_typing(user: dict) -> dict[str, list[str]]:
    """Build synthetic key and value-change logs for email, username, and age."""
    profile = user.get("profile_attributes", {})
    values = {
        "email": user["email"],
        "username": profile.get("username"),
    }
    if profile.get("age") is not None:
        values["age"] = str(profile["age"])

    logs = {}
    for field, value in values.items():
        if not value:
            continue
        events, current = [], ""
        for char in str(value):
            events.append(char)
            current += char
            events.append(f">>{current}<<")
        if events:
            logs[field] = events
    return logs


def _encode_logs(logs: dict[str, list[str]]) -> str:
    """Join field events and Base64-encode their compact UTF-8 JSON representation."""
    joined = {field: "".join(events) for field, events in logs.items()}
    text = json.dumps(joined, ensure_ascii=False, separators=(",", ":"))
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _generate_age() -> int:
    """Generate a random age between 30 and 70, inclusive."""
    return random.randint(30, 70)


def _generate_username() -> str:
    """Generate a username containing 2 to 4 ASCII letters."""
    length = random.randint(2, 4)
    return "".join(random.choices(string.ascii_letters, k=length))


def _generate_password() -> str:
    """
    Generate a password containing 2 to 5 characters using
    only ASCII letters.
    """
    length = random.randint(2, 5)

    return "".join(random.choices(string.ascii_letters, k=length))


def _build_payload(email: str, sign_fn: str) -> dict:
    """Build signup data with generated profile values, signatures, and typing logs."""
    password = _generate_password()
    username = _generate_username()
    age = _generate_age()
    user_data = {
        "email": email,
        "password": password,
        "profile_attributes": {
            "gender": "Male",
            "username": username,
            "location": "Miami, FL, United States",
            "city_id": 1840015149,
            "country": "United States",
            "city": "Miami",
            "state": "FL",
            "latitude": "25.784",
            "longitude": "-80.2102",
            "country_code": "US",
            "age": age,
            "ethnicity": "White",
        },
    }
    logs = _simulate_typing(user_data)
    return {
        "user": user_data,
        "signed": _js_length(email) * _js_length(password),
        "signed2": sum(_codepoints(email + password)),
        "signed3": _compute_signed3(email, sign_fn),
        "changes": _encode_logs(logs),
    }


async def _check(email: str) -> Result:
    """
    Check whether an email address is already registered on Secret Benefits
    by querying the signup flow in multiple steps.
    """
    from user_scanner.core.helpers import get_global_timeout

    timeout = get_global_timeout()
    if timeout is None:
        timeout = 15.0

    show_url = "https://www.secretbenefits.com"
    signup_url = f"{show_url}/signup/man"
    data_url = f"{show_url}/signup/data/man"
    submit_url = f"{show_url}/signup/submit"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    data_headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }

    if not isinstance(email, str):
        return Result.error("Email must be a string", url=show_url)

    async with httpx.AsyncClient(
        http2=False, follow_redirects=True, timeout=timeout
    ) as client:
        try:
            init_resp = await client.get(signup_url, headers=headers)
        except httpx.TimeoutException:
            return Result.error("Signup page request timed out", url=show_url)
        except httpx.RequestError as exc:
            return Result.error(f"Signup page request failed: {exc}", url=show_url)

        if init_resp.status_code == 429:
            return Result.error(
                "Rate limited while accessing signup page", url=show_url
            )
        if not init_resp.is_success:
            return Result.error(
                f"Failed to access signup page: HTTP {init_resp.status_code}",
                url=show_url,
            )

        try:
            data_resp = await client.get(data_url, headers=data_headers)
        except httpx.TimeoutException:
            return Result.error("Signup data request timed out", url=show_url)
        except httpx.RequestError as exc:
            return Result.error(f"Signup data request failed: {exc}", url=show_url)

        if data_resp.status_code == 429:
            return Result.error("Rate limited while fetching signup data", url=show_url)
        if not data_resp.is_success:
            return Result.error(
                f"Failed to fetch signup data: HTTP {data_resp.status_code}",
                url=show_url,
            )

        try:
            data_json = data_resp.json()
        except (ValueError, UnicodeError):
            return Result.error("Signup data response is not valid JSON", url=show_url)

        if not isinstance(data_json, dict):
            return Result.error(
                "Signup data response must be a JSON object", url=show_url
            )

        sign_fn = data_json.get("sign_fn")
        if not isinstance(sign_fn, str) or not sign_fn:
            return Result.error(
                "Missing or invalid sign_fn in signup data", url=show_url
            )

        try:
            payload = _build_payload(email, sign_fn)
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            return Result.error(f"Failed to build signup payload: {exc}", url=show_url)

        try:
            response = await client.post(
                submit_url,
                headers=data_headers,
                json=payload,
            )
        except httpx.TimeoutException:
            return Result.error(
                "Signup submission timed out; server outcome is unknown",
                url=show_url,
            )
        except httpx.RequestError as exc:
            return Result.error(f"Signup submission failed: {exc}", url=show_url)
        except (TypeError, ValueError, UnicodeError):
            return Result.error("Could not encode signup payload", url=show_url)

        try:
            data = response.json()
        except (ValueError, UnicodeError):
            return Result.error(
                "Signup submission response is not valid JSON",
                url=show_url,
            )

        if not isinstance(data, dict):
            return Result.error(
                "Signup submission response must be a JSON object",
                url=show_url,
            )

        error_message = data.get("error_message")
        if isinstance(error_message, str) and error_message.strip():
            return Result.error(error_message, url=show_url)

        errors = data.get("fieldErrors")
        if not isinstance(errors, dict):
            return Result.error(
                "Missing or invalid fieldErrors in submission response",
                url=show_url,
            )

        email_errors = errors.get("email", [])
        if not isinstance(email_errors, list):
            return Result.error(
                "Email errors must be a list of strings",
                url=show_url,
            )

        if "Email is invalid" in email_errors:
            return Result.taken(url=show_url)

        return Result.available(url=show_url)


async def validate_secretbenefits(email: str) -> Result:
    """
    SecretBenefits dating app email validator.
    Checks on the registration endpoint with dummy data.
    """
    return await _check(email)
