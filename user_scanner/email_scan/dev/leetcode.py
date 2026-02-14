import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://leetcode.com/graphql/"
    
    # Hardcoded values as leetcode accepting this value, weird but it works!
    static_csrf = "bMwA82bLs7IrhigK19Bu6uDj4DhZnVnE"
    
    payload = {
        "query": """
            mutation AuthRequestPasswordResetByEmail($email: String!) {
                authRequestPasswordResetByEmail(email: $email) {
                    ok
                    error
                }
            }
        """,
        "variables": {"email": email},
        "operationName": "AuthRequestPasswordResetByEmail"
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'Content-Type': "application/json",
        'x-csrftoken': static_csrf,
        'Origin': "https://leetcode.com",
        'Referer': "https://leetcode.com/accounts/password/reset/",
        'Cookie': f"csrftoken={static_csrf}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            data = response.json()

            result_obj = data.get("data", {}).get("authRequestPasswordResetByEmail", {})
            is_ok = result_obj.get("ok")
            error_msg = result_obj.get("error")

            if is_ok is True:
                return Result.taken()
            
            if is_ok is False and error_msg == "Email does not exist":
                return Result.available()

            return Result.error(f"LeetCode Error: {error_msg}")

    except Exception as e:
        return Result.error(e)

async def validate_leetcode(email: str) -> Result:
    return await _check(email)
