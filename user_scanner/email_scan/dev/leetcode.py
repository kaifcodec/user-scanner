import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://leetcode.com"
    url = "https://leetcode.com/graphql/"

    # Hardcoded values as leetcode accepting this value, weird but it works!
    static_csrf = "bMwA82bLs7IrhigK19Bu6uDj4DhZnVnE"

    # Use signup email validation instead of password reset to avoid sending emails
    payload = {
        "query": """
            query checkIfEmailExist($email: String!) {
                checkIfEmailExist(email: $email)
            }
        """,
        "variables": {"email": email},
        "operationName": "checkIfEmailExist"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Content-Type': "application/json",
        'x-csrftoken': static_csrf,
        'Origin': "https://leetcode.com",
        'Referer': "https://leetcode.com/accounts/signup/",
        'Cookie': f"csrftoken={static_csrf}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            data = response.json()

            # checkIfEmailExist returns true if email is registered, false otherwise
            email_exists = data.get("data", {}).get("checkIfEmailExist")

            if email_exists is True:
                return Result.taken(url=show_url)
            elif email_exists is False:
                return Result.available(url=show_url)

            # Handle potential errors in response
            errors = data.get("errors")
            if errors:
                return Result.error(f"LeetCode Error: {errors[0].get('message', 'Unknown error')}")

            return Result.error("Unexpected response format")

    except Exception as e:
        return Result.error(e)


async def validate_leetcode(email: str) -> Result:
    return await _check(email)
