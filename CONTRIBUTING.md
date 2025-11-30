# Contributing to User-Scanner

Thanks for contributing! This guide explains how to add or modify platform validators correctly, and it includes the new "orchestrator" helpers (generic_validate and status_validate) used to keep validators DRY.

---

## Overview

This project contains small "validator" modules that check whether a username exists on a given platform. Each validator is a single function that returns one of three integer statuses:

- `1` → Username available
- `0` → Username taken
- `2` → Error, blocked, unknown, or request failure

Follow this document when adding or updating validators.

---

## Folder structure

- `social/` -> Social media platforms (Instagram, Reddit, X, etc.)
- `dev/` -> Developer platforms (GitHub, GitLab, Kaggle, etc.)
- `community/` -> Miscellaneous or community-specific platforms
- Add new directories for new categories as needed.

Example:
```
user_scanner/
├── social/
|   └── reddit.py
|    ...
├── dev/
|   └── launchpad.py
|    ...
└── core/
    └── orchestrator.py
     ...
```

Place each new module in the most relevant folder.

---

## Module naming

- File name must be the platform name in lowercase (no spaces or special characters).
  - Examples: `github.py`, `reddit.py`, `x.py`, `pinterest.py`

---

## Validator function

Each module must expose exactly one validator function named:

```python
def validate_<sitename>(user: str) -> int:
    ...
```

Rules:
- Single parameter: the username (str).
- Return values must be integers: `1` (available), `0` (taken), `2` (error).
- Keep the function synchronous unless you are implementing an optional async variant; prefer sync for consistency.
- Prefer using the orchestrator helpers (see below) so validators stay small and consistent.

---

## Orchestrator helpers

To keep validators DRY, the repository provides helper functions in `core/orchestrator.py`. Use these where appropriate.

1. generic_validate
- Purpose: Run a request for a given URL and let a small callback (processor) inspect the httpx.Response and return 1/0/2.

- Typical signature (example — consult the actual orchestrator implementation for exact parameter names):
  - generic_validate(url: str, processor: Callable[[httpx.Response], int], headers: Optional[dict] = None, timeout: float = 5.0, follow_redirects: bool = False) -> int

- Processor function signature:
  - def process(response) -> int
  - Must return 1, 0, or 2.

- Use case: Sites that return 200 for both found and not-found states and require checking the HTML body for a unique "not found" string (e.g., Reddit).

Example reddit module:
```python
from ..core.orchestrator import generic_validate

def validate_reddit(user: str) -> int:
    """
    Checks if a Reddit username is available.
    Strategy: request the user profile page and look for the "not found" message
    because Reddit often returns 200 for both states.
    """
    url = f"https://www.reddit.com/user/{user}/"

    def process(response):
        if response.status_code == 200:
            if "Sorry, nobody on Reddit goes by that name." in response.text:
                return 1
            else:
                return 0
        else:
            return 2

    return generic_validate(url, process, follow_redirects=True)
```

2. status_validate
- Purpose: Simple helper for sites where availability can be determined purely from HTTP status codes (e.g., 404 = available, 200 = taken).
- Typical signature (example):
  - status_validate(url: str, available_status: int, taken_status: int, headers: Optional[dict] = None, timeout: float = 5.0, follow_redirects: bool = False) -> int
- Use case: Sites that reliably return 404 for missing profiles and 200 for existing ones.

Example launchpad module:
```python
from ..core.orchestrator import status_validate

def validate_launchpad(user: str) -> int:
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

Note: The exact parameter names and behavior of the orchestrator functions are defined in `core/orchestrator.py`. Use this CONTRIBUTING guide as a reference for when to use each helper; inspect the orchestrator file if you need detailed signatures.

---

## HTTP requests & headers

- The orchestrator centralizes httpx usage and exception handling. Validators should avoid making raw httpx requests themselves unless there's a specific reason.
- When providing headers, include a User-Agent and reasonable Accept headers.
- Timeouts should be reasonable (3–10 seconds). The orchestrator will usually expose a timeout parameter.

Example common headers:
```py
   headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
      'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9",
      'Accept-Encoding': "gzip, deflate, br, zstd",
      'Upgrade-Insecure-Requests': "1",
   }

```

---

## Return values and error handling

- Always return one of:
  - `1` → available
  - `0` → taken
  - `2` → error / blocked / unknown
- The orchestrator should capture network errors (httpx.ConnectError, httpx.TimeoutException, etc.) and return `2`. If you implement direct requests inside a validator, follow the same exception rules:
```python
except (httpx.ConnectError, httpx.TimeoutException):
    return 2
except Exception:
    return 2
```

---

---

## Style & linting

- Follow PEP8.
- Use type hints for validator signatures.
- Keep code readable and small.
- Add docstrings to explain non-obvious heuristics.
- Run linters and formatters before opening a PR (pre-commit is recommended).

---

## Pull request checklist

Before opening a PR:
- [ ] Add the new validator file in the appropriate folder.
- [ ] Prefer using `generic_validate` or `status_validate` where applicable.
- [ ] Ensure imports are valid and package can be imported.

When opening the PR:
- Describe the approach, any heuristics used, and potential edge cases.
- If the platform has rate limits or anti-bot measures, note them and recommend a testing approach.

---

## When to implement custom logic

- Use `status_validate` when availability is determined by HTTP status codes (e.g., 404 vs 200).
- Use `generic_validate` when you need to inspect response content or headers and decide availability via a short callback.
- If a platform requires API keys, OAuth, or heavy JS rendering, document it in the PR and consider an "advanced" module that can be enabled separately.

---

## Example validator templates

Generic processor style (HTML check):
```python
from ..core.orchestrator import generic_validate

def validate_example(user: str) -> int:
    url = f"https://example.com/{user}"

    def process(resp):
        if resp.status_code == 200:
            if "no such user" in resp.text:
                return 1
            return 0
        elif resp.status_code == 404:
            return 1
        return 2

    return generic_validate(url, process, follow_redirects=True)
```

Status-based style:
```python
from ..core.orchestrator import status_validate

def validate_example2(user: str) -> int:
    url = f"https://example2.com/{user}"
    # 404 => available, 200 => taken
    return status_validate(url, 404, 200, follow_redirects=False)
```

---

Thank you for contributing!
