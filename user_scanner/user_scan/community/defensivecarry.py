import hashlib
import re
from typing import Optional

from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

BASE_URL = "https://www.defensivecarry.com"

CHALLENGE_RE = re.compile(r"(\w+):'([^']*)'")
CHALLENGE_KEYS = (
    "challenge_nonce",
    "challenge_hmac",
    "difficulty",
    "difficulty_char",
    "issued_at",
)
NOT_FOUND_MARKER = "The specified member cannot be found"
PROFILE_PATH_RE = re.compile(r"/members/([^/]+)\.(\d+)/?$")


def validate_defensivecarry(user: str) -> Result:
    url = f"{BASE_URL}/members/"
    params = {"username": user}

    try:
        response = impersonate_request(url, params=params)

        # The site answers 202 with a JavaScript proof-of-work page; solving it
        # and replaying with the pow_bypass cookie returns the real response.
        if response.status_code == 202:
            cookie = _solve_challenge(response.text)
            if not cookie:
                return Result.error("Failed to solve PoW challenge", url=url)
            response = impersonate_request(
                url, params=params, cookies={"pow_bypass": cookie}
            )
    except Exception as e:
        return Result.error(e, url=url)

    # A hit redirects to /members/<slug>.<id>/; a miss re-renders the search page.
    if response.status_code in (301, 302, 303):
        location = response.headers.get("location", "")
        match = PROFILE_PATH_RE.search(location.split("?")[0])
        if not match:
            return Result.error(f"Unexpected redirect target: {location}", url=url)

        profile_url = location if location.startswith("http") else f"{BASE_URL}{location}"
        return Result.taken(
            extra={"handle": match.group(1), "user_id": match.group(2)},
            url=profile_url,
        )

    if response.status_code == 200 and NOT_FOUND_MARKER in response.text:
        return Result.available(url=url)

    return Result.error(f"Unexpected status code: {response.status_code}", url=url)


def _solve_challenge(html_text: str) -> Optional[str]:
    data = dict(CHALLENGE_RE.findall(html_text))
    if any(key not in data for key in CHALLENGE_KEYS):
        return None

    try:
        difficulty = int(data["difficulty"])
    except ValueError:
        return None

    target = data["difficulty_char"] * difficulty
    prefix = data["challenge_nonce"] + data["issued_at"]

    for i in range(1, 10000000):
        digest = hashlib.sha256(f"{prefix}{i}".encode()).hexdigest()
        if digest.startswith(target):
            return (
                f"{data['challenge_nonce']}|{data['issued_at']}|{i}"
                f"|{digest}|{data['challenge_hmac']}"
            )

    return None
