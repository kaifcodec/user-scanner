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

    This function demonstrates how to handle CSRF tokens, custom error
    messages (like IP bans), and passing the target URL back to Results.
    """
    # The display URL used for output and error reporting
    show_url = "https://mastodon.social"

    signup_url = f"{show_url}/auth/sign_up"
    post_url = f"{show_url}/auth"

    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "referer": f"{show_url}/explore",
        "origin": show_url,
    }

    async with httpx.AsyncClient(http2=True, headers=headers, follow_redirects=True) as client:
        try:
            # 1. Access the signup page to retrieve required CSRF tokens
            initial_resp = await client.get(signup_url, timeout=15.0)
            if initial_resp.status_code not in [200, 302]:
                return Result.error(f"Failed to access signup page: {initial_resp.status_code}", url=show_url)

            # Extract the CSRF/authenticity token from the HTML
            token_match = re.search(r'name="csrf-token" content="([^"]+)"', initial_resp.text)
            if not token_match:
                return Result.error("Could not find authenticity token", url=show_url)

            csrf_token = token_match.group(1)

            # 2. Prepare the probe payload with the email we want to check
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
            res_text = response.text
            res_status = response.status_code

            # 3. Analyze the response to determine account status
            if "has already been taken" in res_text:
                return Result.taken(url=show_url)

            elif "registration attempt has been blocked" in res_text:
                return Result.error("Your IP has been flagged by Mastodon", url=show_url)

            elif res_status == 429:
                return Result.error("Rate limited; try using the '-d' flag", url=show_url)

            elif res_status in [200, 302]:
                # If no 'taken' message is found and status is OK/Redirect, it's available
                return Result.available(url=show_url)

            else:
                return Result.error("Unexpected response body", url=show_url)

        except Exception as exc:
            # Always pass the url=show_url even in exceptions for clear reporting
            return Result.error(str(exc), url=show_url)


async def validate_mastodon(email: str) -> Result:
    """
    Public validator used by the email mode.

    All email modules must export a 'validate_<name>' function that
    returns a Result object.
    """
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

**CRITICAL Rules for `user_scan` Modules:**

1. **Explicit Verification (No False Positives):** Never rely solely on a generic HTTP 200 to assume availability. Many WAFs and CDNs intercept requests and return 200 OK. You MUST explicitly verify a unique string or JSON key for BOTH the `taken` and `available` states. **Never use a bare `else: return Result.available()` block.**
2. **Deep Data Extraction:** If the user is found, attempt to extract rich metadata (fullname, location, bio, stats) and return it via `Result.taken(extra={"fullname": "John Doe", ...})`.
3. **Strict Error Handling:** NEVER use `raise Exception()`. All unhandled states or unexpected status codes must return `Result.error(f"Unexpected status code {resp.status_code}")`.
4. **Use Orchestrator Helpers:** Use `generic_validate` to standardize `httpx` logic, but write robust `process` callbacks.

---

## Orchestrator helpers (user_scan)

To keep validators DRY, the repository provides helper functions in `core/orchestrator.py`.

### 1. generic_validate (Preferred)

- **Purpose:** Run a request for a given URL and let a callback (`process`) inspect the `httpx.Response` and return a `Result`.
- **Use case:** Highly recommended for all modern modules to inspect response content, prevent false positives, and parse out deep data.

### Example robust module with deep data extraction:

```python
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
import re
import json

def validate_example(user: str) -> Result:
    url = f"https://www.example.com/{user}/profile"
    show_url = "https://www.example.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    def process(response):
        # 1. Explicitly check for the "not found" state
        if response.status_code == 404 or "User does not exist" in response.text:
            return Result.available()
            
        # 2. Explicitly verify the "taken" state and extract deep data
        if response.status_code == 200 and "profile-data" in response.text:
            extra = {}
            match = re.search(r'<script id="profile-data">({.+?})</script>', response.text)
            if match:
                data = json.loads(match.group(1))
                if "name" in data:
                    extra["fullname"] = data["name"]
                if "location" in data:
                    extra["location"] = data["location"]
            return Result.taken(extra=extra)

        # 3. Graceful error handling for unexpected states (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
```

### 2. status_validate (Discouraged)

- **Purpose:** Simple helper for sites where availability can be determined purely from HTTP status codes (e.g., 404 = available, 200 = taken).
- **Warning:** Use this *only* as a last resort if the site has absolutely no WAF and reliably returns strict HTTP codes without custom redirect/error pages. Modern sites heavily punish this approach.

---

## Return values and error handling

- Always return a Result object:
  - `Result.available()`
  - `Result.taken(extra={"fullname": "..."})`
  - `Result.error("short diagnostic message")`
- The orchestrator captures network errors (`httpx.ConnectError`, `httpx.TimeoutException`, etc.) and returns `Result.error(...)` automatically.
- **NEVER** use `raise Exception("...")`. If you encounter an anomaly in your `process` function, always return `Result.error("...")` so the scanner can gracefully continue to the next module.

---

## Style & linting

- Follow PEP8.
- Use type hints for validator signatures.
- Keep code readable and small.
- Add docstrings to explain non-obvious heuristics.
- Run linters and formatters before opening a PR (pre-commit is recommended).

---

Thank you for contributing!
