# Contributing to user-scanner

---

This project separates two kinds of checks:

- Username availability checks (under `user_scanner/user_scan/*`) — synchronous validators that the main username scanner uses.
- Email OSINT checks (under `user_scanner/email_scan/`) — asynchronous, multi-step flows that probe signup pages or email-focused APIs. Put email-focused modules in `user_scanner/email_scan/` (subfolders like `social/`, `dev/`, `community`, `creator` etc. are fine — follow the existing tree).


---

## Module naming for both `email_scan` and `user_scan` modules

- File name must be the platform name in lowercase (no spaces or special characters).
  - Examples: `github.py`, `reddit.py`, `x.py`, `pinterest.py`

---


## Email-scan (email_scan) — guide for contributors

Minimal best-practices checklist for email modules
- [ ] Put file in `user_scanner/email_scan/<category>/service.py`.
- [ ] Export `async def validate_<service>(email: str) -> Result`.
- [ ] Use `httpx.AsyncClient` for requests, with sensible timeouts and follow_redirects when needed.
- [ ] Add a short docstring describing environment variables (api keys), rate limits, and responsible-use note (if required)

### Example: Mastodon async example:

```python name=user_scanner/email_scan/social/mastodon.py
import httpx
import re
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    """
    Internal helper that performs the multi-step signup probe.
    Returns: Result.available(), Result.taken(), or Result.error(msg)
    """
    base_url = "https://mastodon.social"
    signup_url = f"{base_url}/auth/sign_up"
    post_url = f"{base_url}/auth"

    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "referer": "https://mastodon.social/explore",
        "origin": "https://mastodon.social",
    }

    async with httpx.AsyncClient(http2=True, headers=headers, follow_redirects=True) as client:
        try:
            initial_resp = await client.get(signup_url, timeout=15.0)
            if initial_resp.status_code != 200:
                return Result.error(f"Failed to access signup page: {initial_resp.status_code}")

            # Look for CSRF/auth token in the signup HTML
            token_match = re.search(r'name="csrf-token" content="([^"]+)"', initial_resp.text)
            if not token_match:
                return Result.error("Could not find authenticity token")

            csrf_token = token_match.group(1)

            # Use a dummy username & password for the signup probe
            payload = {
                "authenticity_token": csrf_token,
                "user[account_attributes][username]": "no3motions_robot_020102",
                "user[email]": email,
                "user[password]": "Theleftalone@me",
                "user[password_confirmation]": "Theleftalone@me",
                "user[agreement]": "1",
                "button": ""
            }

            response = await client.post(post_url, data=payload, timeout=15.0)

            # Check the response HTML for the "already taken" phrase
            if "has already been taken" in response.text:
                return Result.taken()
            else:
                # If the response does not show taken, treat as available.
                # Be aware: services can change wording; prefer explicit checks.
                return Result.available()

        except Exception as exc:
            # Convert exception to string so Result.error is stable/serializable
            return Result.error(str(exc))


async def validate_mastodon(email: str) -> Result:
    """
    Public validator used by the email mode.
    - Do basic local validation before network calls.
    - Return Result.* helpers described above.
    """
    if not EMAIL_RE.match(email):
        return Result.error("Invalid email format")
    return await _check(email)
```


---

## Username availability check guide:


### Validator function (user_scan/)

Each module must expose exactly one validator function named:

```python
def validate_<sitename>(user: str) -> Result:
    ...
```

Rules:
- Single parameter: the username (str).
- Return a Result object (use Result.available(), Result.taken(), or Result.error(msg)).
- Keep the function synchronous unless you are implementing an optional async variant; prefer sync for consistency.
- Prefer using the orchestrator helpers (see below) so validators stay small and consistent.

---

## Orchestrator helpers (user_scan)

To keep validators DRY, the repository provides helper functions in `core/orchestrator.py`. Use these where appropriate.

1. generic_validate
- Purpose: Run a request for a given URL and let a small callback (processor) inspect the httpx.Response and return a Result.
- Typical signature (example — consult the actual orchestrator implementation for exact parameter names):
  - `generic_validate(url: str, processor: Callable[[httpx.Response], Result], headers: Optional[dict] = None, timeout: float = 5.0, follow_redirects: bool = False) -> Result`
- Processor function signature:
  - def process(response) -> Result
  - Must return Result.available(), Result.taken(), or Result.error("message")
- Use case: Sites that return 200 for both found and not-found states and require checking the HTML body for a unique "not found" string (or other content inspection).

### Example `github.py` module:
- This example shows how to use `generic_validate()` and how to return Result values with optional error messages.

```python
from user_scanner.core.orchestrator import generic_validate, Result


def validate_github(user):
    url = f"https://github.com/signup_check/username?value={user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua-platform': "\"Linux\"",
        'sec-ch-ua': "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://github.com/signup?source=form-home-signup&user_email=",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }

    GITHUB_INVALID_MSG = (
        "Username may only contain alphanumeric characters or single hyphens, "
        "and cannot begin or end with a hyphen."
    )

    def process(response):
        if response.status_code == 200:
            return Result.available()

        if response.status_code == 422:
            if GITHUB_INVALID_MSG in response.text:
                return Result.error("Cannot start/end with hyphen or use double hyphens")

            return Result.taken()

        return Result.error("Unexpected GitHub response — report it via issues")

    return generic_validate(url, process, headers=headers)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_github(user)

    # Inspect Result (example usage; adapt to actual Result API in orchestrator)
    if result == Result.available():
        print("Available!")
    elif result == Result.taken():
        print("Unavailable!")
    else:
        # Result.error can carry a message; show it when present
        msg = getattr(result, "message", None)
        print("Error occurred!" + (f" {msg}" if msg else ""))
```

2. status_validate
- Purpose: Simple helper for sites where availability can be determined purely from HTTP status codes (e.g., 404 = available, 200 = taken).
- Typical signature (example):
  - `status_validate(url: str, available_status: int, taken_status: int, headers: Optional[dict] = None, timeout: float = 5.0, follow_redirects: bool = False) -> Result`
- Use case: Sites that reliably return 404 for missing profiles and 200 for existing ones.

### Example `launchpad.py` module:

```python
from user_scanner.core.orchestrator import status_validate

def validate_launchpad(user: str):
    """
    Uses status_validate because Launchpad returns 404 for non-existing users
    and 200 for existing ones.
    """
    url = f"https://launchpad.net/~{user}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Upgrade-Insecure-Requests": "1",
    }

    # available_status=404, taken_status=200
    return status_validate(url, 404, 200, headers=headers, follow_redirects=True)
```

Note: The exact parameter names and behavior of the orchestrator functions are defined in `core/orchestrator.py`. Use this CONTRIBUTING guide as a reference for when to use each helper; inspect the implementation for exact types and helper methods on Result.

---

## HTTP requests & headers

- The orchestrator centralizes httpx usage and exception handling. Validators should avoid making raw httpx requests themselves unless there's a specific reason.
- When providing headers, include a User-Agent and reasonable Accept headers.
- Timeouts should be reasonable (3–10 seconds). The orchestrator will usually expose a timeout parameter.

---

## When to implement custom logic (user_scan)

- Use `status_validate` when availability is determined by HTTP status codes (e.g., 404 vs 200).
- Use `generic_validate` when you need to inspect response content or headers and decide availability via a short callback that returns a Result.
- If a platform requires API keys, OAuth, or heavy JS rendering, document it in the PR and consider an "advanced" module that can be enabled separately.

---


## Return values and error handling

- Always return a Result object:
  - Result.available()
  - Result.taken()
  - Result.error("short diagnostic message")
- The orchestrator will capture network errors (httpx.ConnectError, httpx.TimeoutException, etc.) and should return Result.error(...) for those cases. If you implement direct requests inside a validator, follow the same pattern:

```python
except (httpx.ConnectError, httpx.TimeoutException):
    return Result.error("network error")
except Exception:
    return Result.error("unexpected error")
```

- Prefer returning meaningful error messages with Result.error to help debugging and triage in issues.

---

## Style & linting

- Follow PEP8.
- Use type hints for validator signatures.
- Keep code readable and small.
- Add docstrings to explain non-obvious heuristics.
- Run linters and formatters before opening a PR (pre-commit is recommended).

---

Thank you for contributing!
