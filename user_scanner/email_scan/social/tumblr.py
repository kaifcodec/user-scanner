import asyncio
import re

from curl_cffi import requests

from user_scanner.core.result import Result

# The public web app's bearer token, embedded in the homepage HTML.
API_TOKEN_RE = re.compile(r'"API_TOKEN":"([^"]+)"')
VALIDATE_URL = "https://www.tumblr.com/api/v2/register/account/validate"

# response codes returned by the account-validate endpoint.
USER_EXISTS = 2
PASSWORD_TOO_SHORT = 1030


def _check_sync(email: str) -> Result:
    show_url = "https://tumblr.com"

    # Use curl_cffi to impersonate a real Chrome browser
    session: requests.Session = requests.Session(impersonate="chrome131", timeout=15.0)

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive',
    }

    try:
        # 1. Get Home Page to extract API token
        response = session.get("https://www.tumblr.com/", headers=headers)
        html = response.text

        token_match = API_TOKEN_RE.search(html)
        if not token_match:
            return Result.error("Token extraction failed, report it via GitHub issues")
        token = token_match.group(1)

        # 2. Get Radar to extract CSRF
        radar_headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authorization': f"Bearer {token}",
            'Origin': 'https://www.tumblr.com',
            'Referer': 'https://www.tumblr.com/',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        }
        response2 = session.get("https://www.tumblr.com/api/v2/radar", headers=radar_headers)
        csrf = response2.headers.get("X-Csrf")
        
        if not csrf:
            return Result.error("CSRF extraction failed, report it via GitHub issues")

        # 3. Post Account Validate
        validate_headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {token}",
            'X-CSRF': csrf,
            'Origin': 'https://www.tumblr.com',
            'Referer': 'https://www.tumblr.com/register',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        }

        payload = {
            'email': email,
            'password': "Password123!@#",
            'tumblelog': "osintuserprobe"
        }

        response3 = session.post(
            VALIDATE_URL,
            headers=validate_headers,
            json=payload
        )

        if response3.status_code != 200:
            return Result.error(f"Unexpected HTTP status: {response3.status_code}")

        response_data = response3.json()
        # If the response is directly the object (not wrapped in "response")
        if "response" in response_data:
            data = response_data.get("response")
        else:
            data = response_data

        # If the response is an empty list, it means the email is available
        if not data or data == []:
            return Result.available(url=show_url)

        if not isinstance(data, dict):
            return Result.error(f"Invalid API response format: {data}")

        code = data.get("code")
        error_msg = str(data.get("error", "")).lower()

        if code == USER_EXISTS and "user already exists" in error_msg:
            return Result.taken(url=show_url)
        elif code == PASSWORD_TOO_SHORT and "password" in error_msg:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected response (code: {code}, error: {error_msg}), report it via GitHub issues")

    except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
        return Result.error(f"unexpected exception: {e}")


async def validate_tumblr(email: str) -> Result:
    try:
        return await asyncio.to_thread(_check_sync, email)
    except (requests.exceptions.RequestException, ValueError, TypeError) as e:
        return Result.error(f"unexpected exception: {e}")