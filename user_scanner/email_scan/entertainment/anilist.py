import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    show_url = "https://anilist.co"
    url = "https://anilist.co/graphql"

    payload = {
        "query": "mutation($email:String){ResetPassword(email:$email)}",
        "variables": {
            "email": email
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'schema': "internal",
        'origin': "https://anilist.co",
        'referer': "https://anilist.co/forgot-password",
        'accept-language': "en-US,en;q=0.9"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            data = response.json()
            errors = data.get("errors", [])

            if not errors:
                return Result.error("Unexpected response body structure (No errors returned)")

            error_msg = errors[0].get("message", "").lower()

            if "unauthorized" in error_msg:
                return Result.taken(url=show_url)

            elif "validation" in error_msg:
                validation = errors[0].get("validation", {})
                email_errors = validation.get("email", [])
                if any("invalid" in e.lower() for e in email_errors):
                    return Result.available(url=show_url)

                return Result.error("Unexpected validation error message")

            else:
                return Result.error(f"Unexpected error type: {error_msg}, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)

async def validate_anilist(email: str) -> Result:
    return await _check(email)
