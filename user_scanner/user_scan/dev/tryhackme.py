import json

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_tryhackme(user: str) -> Result:
    """
    Checks TryHackMe username availability via the public-profile API.

    TryHackMe sits behind Vercel's bot-mitigation firewall, which blocks
    plain httpx/curl requests on TLS-fingerprint grounds (observed as an
    HTTP 429 with an `x-vercel-mitigated: challenge` header, not a real
    app-level rate limit). We use impersonate_validate to route the
    request through a Chrome-TLS-impersonating curl_cffi session so it
    passes that check.

    The /p/<username> HTML page itself is a client-rendered Next.js shell
    that's identical regardless of whether the user exists (profile data
    loads afterward via JS), so scraping it produces false positives.
    Instead we hit the same JSON API the frontend calls directly:

        GET https://tryhackme.com/api/v2/public-profile?username=<user>

    A nonexistent user returns 200 with {"status": "error", "message":
    "Profile not found"}. An existing user returns 200 with
    {"status": "success", "data": {...profile fields...}}.
    """
    url = "https://tryhackme.com/api/v2/public-profile"
    show_url = f"https://tryhackme.com/p/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        try:
            data = response.json()
        except json.JSONDecodeError:
            return Result.error("Non-JSON response body (possible WAF challenge)")

        status = data.get("status")

        if status == "error":
            # Explicitly confirm this is the "not found" case rather than
            # assuming any error means available.
            message = str(data.get("message", ""))
            if "not found" in message.lower():
                return Result.available()
            return Result.error(f"API error: {message}")

        if status == "success":
            profile = data.get("data") or {}
            extra = {}

            if profile.get("level") is not None:
                extra["level"] = profile.get("level")
            if profile.get("totalPoints") is not None:
                extra["points"] = profile.get("totalPoints")
            if profile.get("rank") is not None:
                extra["rank"] = profile.get("rank")
            if profile.get("completedRoomsNumber") is not None:
                extra["rooms_completed"] = profile.get("completedRoomsNumber")
            if profile.get("streak") is not None:
                extra["streak"] = profile.get("streak")
            if profile.get("country"):
                extra["country"] = profile.get("country")

            media = {}
            if profile.get("avatar"):
                media["avatar"] = profile.get("avatar")

            return Result.taken(extra=extra, media=media)

        return Result.error(f"Unrecognized API response shape: {data}")

    return impersonate_validate(
        url,
        process,
        warmup_url="https://tryhackme.com/",
        impersonate="chrome",
        show_url=show_url,
        allow_redirects=True,
        params={"username": user},
    )
