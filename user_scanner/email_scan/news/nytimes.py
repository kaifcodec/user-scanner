import httpx
import json
import re
import html
from user_scanner.core.result import Result


async def _check(email: str) -> Result:

    login_url = "https://myaccount.nytimes.com/auth/enter-email?response_type=cookie&client_id=vi&redirect_uri=https%3A%2F%2Fwww.nytimes.com"
    check_url = "https://myaccount.nytimes.com/svc/lire_ui/authorize-email/check"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            init_res = await client.get(login_url, headers=headers)

            token_match = re.search(
                r'authToken(?:&quot;|"):(?:&quot;|")([^&"]+)', init_res.text)

            if not token_match:
                return Result.error("Could not extract NYT auth_token")

            auth_token = html.unescape(token_match.group(1))

            payload = {
                "email": email,
                "abraTests": "{\"AUTH_new_regilite_flow\":\"1_Variant\",\"AUTH_FORGOT_PASS_LIRE\":\"1_Variant\",\"AUTH_B2B_SSO\":\"1_Variant\"}",
                "auth_token": auth_token,
                "form_view": "enterEmail",
                "environment": "production"
            }

            # Update headers for the API call
            api_headers = headers.copy()
            api_headers.update({
                'Content-Type': "application/json",
                'Accept': "application/json",
                'req-details': "[[it:lui]]",
                'Origin': "https://myaccount.nytimes.com",
                'Referer': login_url
            })

            response = await client.post(check_url, content=json.dumps(payload), headers=api_headers)
            data = response.json()

            further_action = data.get("data", {}).get("further_action", "")

            if further_action == "show-login":
                return Result.taken()
            elif further_action == "show-register":
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)


async def validate_nytimes(email: str) -> Result:
    return await _check(email)
