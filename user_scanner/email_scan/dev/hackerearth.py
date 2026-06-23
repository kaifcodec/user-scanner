import httpx
import secrets
from user_scanner.core.result import Result

def _generate_random_name() -> tuple[str, str]:
    """Generates short random names to keep individual payloads unique."""
    first_names = ["Hunan", "Hedge", "Zack", "Dex", "Jace", "Kira", "Cole", "Finn", "Nuter"]
    last_names = ["Fish", "Code", "Byte", "Web", "Null", "Dev", "Node", "Flux", "Jones"]
    return secrets.choice(first_names), secrets.choice(last_names)

async def _check(email: str) -> Result:
    url = "https://www.hackerearth.com/api/v1/sparta/auth/signup/"
    show_url = "https://www.hackerearth.com"

    first, last = _generate_random_name()

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "gzip, deflate",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'sec-gpc': "1",
        'accept-language': "en-US,en;q=0.7",
        'origin': "https://www.hackerearth.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': show_url,
        'priority': "u=1, i"
    }

    params = {
        'sxhr': "true",
        'next': "/community/dashboard/"
    }

    payload = {
        "first_name": first,
        "last_name": last,
        "email": email,
        "password": "",  # Blank to force targeted validation errors
        "policy_accepted": True,
        "next": "/community/dashboard/"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF (403)")
            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response")

            errors = data.get("errors", {})
            email_error = errors.get("email", "")

            # If 'email' key exists in errors with the taken string -> Taken
            if "already registered" in email_error.lower():
                return Result.taken(url=show_url)

            # If password error exists but email error does not -> Email is available
            if "password" in errors and not email_error:
                return Result.available(url=show_url)

            return Result.error("Unexpected response field layout")

    except Exception as e:
        return Result.error(str(e))

async def validate_hackerearth(email: str) -> Result:
    return await _check(email)
