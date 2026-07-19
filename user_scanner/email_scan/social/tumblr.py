import re
import urllib.request
import urllib.error
import json
import asyncio
from user_scanner.core.result import Result

# The public web app's bearer token, embedded in the homepage HTML.
API_TOKEN_RE = re.compile(r'"API_TOKEN":"([^"]+)"')
VALIDATE_URL = "https://www.tumblr.com/api/v2/register/account/validate"

# response codes returned by the account-validate endpoint. A deliberately
# short password means a free email always trips PASSWORD_TOO_SHORT (so no
# account is created), while a taken email trips USER_EXISTS first regardless.
USER_EXISTS = 2
PASSWORD_TOO_SHORT = 1030


def _check_sync(email: str) -> Result:
    show_url = "https://tumblr.com"
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
    }
    try:
        # 1. Get Home Page
        req = urllib.request.Request("https://www.tumblr.com/", headers=headers)
        with urllib.request.urlopen(req, timeout=15.0) as response:
            html = response.read().decode("utf-8")
        
        token_match = API_TOKEN_RE.search(html)
        if not token_match:
            return Result.error("Token extraction failed, report it via GitHub issues")
        token = token_match.group(1)

        # 2. Get Radar to extract CSRF
        req2 = urllib.request.Request("https://www.tumblr.com/api/v2/radar", headers={
            **headers,
            'Authorization': f"Bearer {token}"
        })
        with urllib.request.urlopen(req2, timeout=15.0) as response2:
            csrf = response2.headers.get("X-Csrf")
        if not csrf:
            return Result.error("CSRF extraction failed, report it via GitHub issues")

        # 3. Post Account Validate
        req3 = urllib.request.Request(
            VALIDATE_URL,
            headers={
                **headers,
                'Authorization': f"Bearer {token}",
                'X-CSRF': csrf,
                'Content-Type': "application/json",
                'Accept': "application/json",
                'Origin': "https://www.tumblr.com",
                'Referer': "https://www.tumblr.com/register",
            },
            data=json.dumps({'email': email, 'password': "x", 'tumblelog': "osintuserprobe"}).encode("utf-8"),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req3, timeout=15.0) as response3:
                res_body = response3.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                res_body = e.read().decode("utf-8")
            else:
                return Result.error(f"Unexpected HTTP status: {e.code}")
        
        data = json.loads(res_body).get("response")
        if not isinstance(data, dict):
            return Result.error("Invalid API response format, response is not a dict")
            
        code = data.get("code")
        error_msg = str(data.get("error", "")).lower()
        
        # Check both response code and the description message to prevent false positives if the structure changes
        if code == USER_EXISTS and "user already exists" in error_msg:
            return Result.taken(url=show_url)
        elif code == PASSWORD_TOO_SHORT and "password" in error_msg:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected response (code: {code}, error: {error_msg}), report it via GitHub issues")

    except Exception as e:
        return Result.error(f"unexpected exception: {e}")


async def validate_tumblr(email: str) -> Result:
    try:
        return await asyncio.to_thread(_check_sync, email)
    except Exception as e:
        return Result.error(f"unexpected exception: {e}")
