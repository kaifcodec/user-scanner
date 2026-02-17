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
  - `generic_validate(url: str, processor: Callable[[httpx.Response], Result], headers: Optional[dict] = None, show_url=None, timeout: float = 5.0, follow_redirects: bool = False) -> Result`
- Processor function signature:
  - def process(response) -> Result
  - Must return Result.available(), Result.taken(), or Result.error("message")
- Use case: Sites that return 200 for both found and not-found states and require checking the HTML body for a unique "not found" string (or other content inspection).

### Example `github.py` module:
- This example shows how to use `generic_validate()` and how to return Result values with optional error messages.

```python
from user_scanner.core.orchestrator import generic_validate, Result

def validate_github(user: str) -> Result:
    """
    Example of a 'generic_validate' module.
    Use this when the site requires complex logic or response body parsing.
    """
    url = f"https://github.com/signup_check/username?value={user}"
    
    # Define show_url for clean output display
    show_url = "https://github.com"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'referer': "https://github.com/signup",
        'accept-language': "en-US,en;q=0.9",
    }

    # Specific error message from GitHub for validation rules
    GITHUB_INVALID_MSG = (
        "Username may only contain alphanumeric characters or single hyphens, "
        "and cannot begin or end with a hyphen."
    )

    def process(response):
        """
        Internal processing function.
        Note: You don't need to pass 'url' here; 
        generic_validate will attach it automatically from the kwargs.
        """
        if response.status_code == 200:
            return Result.available()

        if response.status_code == 422:
            if GITHUB_INVALID_MSG in response.text:
                return Result.error("Invalid format: alphanumeric and single hyphens only")

            return Result.taken()

        return Result.error(f"GitHub returned unexpected status: {response.status_code}")

    # Pass show_url into generic_validate so the Orchestrator 
    # can attach it to the final Result object.
    return generic_validate(url, process, headers=headers, show_url=show_url)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_github(user)

    if result.is_available():
        print("Available!")
    elif result.is_taken():
        print(f"Unavailable! Site: {result.url}")
    else:
        print(f"Error: {result.get_reason()}")

```

2. status_validate
- Purpose: Simple helper for sites where availability can be determined purely from HTTP status codes (e.g., 404 = available, 200 = taken).
- Typical signature (example):
  - `status_validate(url: str, available_status: int, taken_status: int, show_url=None, headers: Optional[dict] = None, timeout: float = 5.0, follow_redirects: bool = False) -> Result`
- Use case: Sites that reliably return 404 for missing profiles and 200 for existing ones.

### Example `launchpad.py` module:

```python
from user_scanner.core.orchestrator import status_validate


def validate_launchpad(user):
    url = f"https://launchpad.net/~{user}"
    show_url = "https://launchpad.net"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Upgrade-Insecure-Requests': "1",
    }

    return status_validate(url, 404, 200, show_url=show_url, headers=headers, follow_redirects=True)
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
