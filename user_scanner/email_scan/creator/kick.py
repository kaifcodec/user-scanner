import httpx
import secrets
from user_scanner.core.result import Result

def _generate_trace_id() -> str:
    """Generates a 32-character hexadecimal string to emulate a real mobile tracing token."""
    return secrets.token_hex(16)

async def _check(email: str) -> Result:
    url = "https://kick.com/api/v1/signup/verify/email"
    show_url = "https://kick.com/"

    headers = {
        'User-Agent': "KickMobile/40.18.1 (com.kick.mobile; platform: android; build:60006868)",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'cache-control': "no-store",
        'x-app-platform': "Android",
        'x-app-version': "40.18.1",
        'x-kick-app': "mobile",
        'x-req-trace': _generate_trace_id()
    }

    payload = {
        "email": email
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            # Check for generic perimeter blocks
            if response.status_code == 403:
                return Result.error("Caught by Cloudflare WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited by Kick (429)")

            # Target validation logic (Status 204 No Content -> Email is available)
            if response.status_code == 204:
                return Result.available(url=show_url)

            if response.status_code == 422:
                try:
                    data = response.json()
                    errors = data.get("errors", {})
                    email_errors = errors.get("email", [])

                    if any("already been taken" in str(err).lower() for err in email_errors):
                        return Result.taken(url=show_url)
                except Exception:
                    return Result.error("Failed to parse 422 validation content")

            return Result.error(f"Unexpected response state (HTTP {response.status_code})")

    except Exception as e:
        return Result.error(str(e))

async def validate_kick(email: str) -> Result:
    return await _check(email)
