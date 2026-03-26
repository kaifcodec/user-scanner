import httpx
import json
import re
import html
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://nytimes.com"
    # hit this first to wake up the session and grab the token
    login_url = "https://myaccount.nytimes.com/auth/enter-email?response_type=cookie&client_id=vi&redirect_uri=https%3A%2F%2Fwww.nytimes.com"
    check_url = "https://myaccount.nytimes.com/svc/lire_ui/authorize-email/check"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
        'Accept-Encoding': "identity",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': "?1"
    }

    try:
        # NYT likes HTTP/2, helps avoid getting flagged as a bot
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, http2=True) as client:

            init_res = await client.get(login_url, headers=headers)

            if init_res.status_code == 403:
                return Result.error("NYT blocked the initial hit (403)")

            # Digging out the auth_token from the mess of HTML/JS
            token_match = re.search(
                r'authToken(?:&quot;|"|\\")\s*:\s*(?:&quot;|"|\\")([^&"\\]+)',
                init_res.text
            )

            if not token_match:
                return Result.error("Couldn't find the auth_token in the page")

            auth_token = html.unescape(token_match.group(1))

            payload = {
                "email": email,
                "abraTests": "{\"AUTH_new_regilite_flow\":\"1_Variant\",\"AUTH_FORGOT_PASS_LIRE\":\"1_Variant\",\"AUTH_B2B_SSO\":\"1_Variant\"}",
                "auth_token": auth_token,
                "form_view": "enterEmail",
                "environment": "production"
            }

            # The critical tracking/origin headers
            api_headers = headers.copy()
            api_headers.update({
                'Content-Type': "application/json",
                'Accept': "application/json",
                'req-details': "[[it:lui]]",
                'Origin': "https://myaccount.nytimes.com",
                'Referer': login_url,
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty"
            })

            response = await client.post(
                check_url,
                content=json.dumps(payload),
                headers=api_headers
            )

            if response.status_code == 403:
                return Result.error("Bot detection triggered on the check (403)")

            if response.status_code != 200:
                return Result.error(f"API acted up: {response.status_code}")

            res_data = response.json()
            further_action = res_data.get("data", {}).get("further_action", "")

            # If it says show-login, they have an account. If show-register, they don't.
            if further_action == "show-login":
                return Result.taken(url=show_url)
            elif further_action == "show-register":
                return Result.available(url=show_url)

            return Result.error(f"Got an weird action: {further_action}")

    except httpx.ReadTimeout:
        return Result.error("NYT took too long to answer")
    except Exception as e:
        return Result.error(e)


async def validate_nytimes(email: str) -> Result:
    return await _check(email)
