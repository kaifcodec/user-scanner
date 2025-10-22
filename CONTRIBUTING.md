# Contributing to User-Scanner

Thanks for contributing! This guide explains how to add or modify platform validators correctly.

---

## Folder Structure

- `social/` -> Social media platforms (Instagram, Reddit, Twitter, etc.)
- `tech/` -> Tech platforms (GitHub, GitLab, Kaggle, etc.)
- `community/`  -> Miscellaneous or community-specific platforms
- ...
- ...
- Create new directories for new category sites.

All new modules should be placed in the relevant folder.

Example structure:
```
user_scanner/
├── social/
│   └── <platform>.py
├── tech/
│   └── <platform>.py
└── community/
    └── <platform>.py
```

---

## Module Naming

- Each file should be named exactly after the platform, in lowercase.
  - Examples: `github.py`, `reddit.py`, `x.py`, `pinterest.py`
- Avoid spaces, special characters, or uppercase letters.

---

## Validator Function

Each module must contain **one validator function**:

- Function name format: `validate_<sitename>()`
  - Example: `validate_github(user)` or `validate_x(user)`
- Signature:
```python
def validate_<sitename>(user: str) -> int:
    ...
```
- Return values:
  - `1` → Username **available**
  - `0` → Username **taken**
  - `2` → Error, blocked, or unknown
- Only accepts a single argument: the username string.
- Keep it **synchronous** (async optional for advanced modules).

---

## HTTP Requests

- Use `httpx` for requests.
- Set a reasonable timeout (e.g., 3–15 seconds).
- Include a User-Agent header.
- Catch exceptions and return `2` for errors:
```python
except (httpx.ConnectError, httpx.TimeoutException):
    return 2
except Exception:
    return 2
```

---

## Style Guidelines

- Keep code clean and readable.
- Follow **PEP8** conventions.

---

## Example Modules

### 1. HTML string check (Reddit)
```python
import httpx

def validate_reddit(user):
    """
    Checks if a Reddit username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """
    url = f"https://www.reddit.com/user/{user}/"
    NOT_FOUND = "Sorry, nobody on Reddit goes by that name."

    try:
        r = httpx.get(url, timeout=3.0, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return 1 if NOT_FOUND in r.text else 0
        return 2
    except:
        return 2
```

**Notes:**  
- Some platforms always return 200; check for a **unique string** in the HTML that only appears for non-existent usernames.  
- Prefer **official API endpoints** if available.

---

### 2. HTTP status check (Launchpad)
```python
import httpx

def validate_launchpad(user):
    """
    Checks if a Launchpad username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """
    url = f"https://launchpad.net/~{user}"

    try:
        r = httpx.head(url, timeout=5, follow_redirects=True)
        if r.status_code == 404:
            return 1  # available
        elif r.status_code == 200:
            return 0  # taken
        return 2
    except:
        return 2
```

**Notes:**  
- HTTP status `404` usually → available, `200` → taken.  
- HEAD request is sufficient, avoids downloading full HTML.

---

Following these guidelines ensures that **all validators are compatible with the orchestrator** and run correctly for the username scan.
