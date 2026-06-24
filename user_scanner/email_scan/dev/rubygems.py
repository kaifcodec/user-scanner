import httpx
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url_signup = "https://rubygems.org/sign_up"
    url_users = "https://rubygems.org/users"
    show_url = "https://rubygems.org"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua': '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-platform': '"Android"',
        'upgrade-insecure-requests': "1",
        'sec-gpc': "1",
        'accept-language': "en-US,en;q=0.7",
        'origin': "https://rubygems.org",
        'referer': url_signup
    }

    try:
        # Using a unified client session context to automatically hold and pass back the _rubygems_session cookie
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:

            # Initialize session state and extract Rails CSRF token
            init_res = await client.get(url_signup, headers=headers)
            if init_res.status_code != 200:
                return Result.error(f"Failed to grab verification context: {init_res.status_code}")

            # Extract the authenticity token from the hidden input element field
            token_match = re.search(r'name="authenticity_token" value="([^"]+)"', init_res.text)
            if not token_match:
                return Result.error("Could not scrape Rails authenticity token")
            
            csrf_token = token_match.group(1)

            # Fire validation payload with empty password gate
            payload = {
                'authenticity_token': csrf_token,
                'user[full_name]': "",
                'user[email]': email,
                'user[handle]': "",
                'user[password]': "",
                'user[public_email]': "0",
                'commit': "Sign up"
            }

            response = await client.post(url_users, data=payload, headers=headers)
            response_text = response.text

            # Targeted field-level string verification inside the generated #errorExplanation block
            if "has already been taken" in response_text:
                return Result.taken(url=show_url)

            # If Rails triggers validation errors but email is NOT flagged as taken, the target is clear
            if "prohibited this user from being saved" in response_text or "Password can't be blank" in response_text:
                return Result.available(url=show_url)

            return Result.error("Unexpected signature inside response DOM tree")

    except Exception as e:
        return Result.error(str(e))

async def validate_rubygems(email: str) -> Result:
    return await _check(email)
