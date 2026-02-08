import httpx
import re
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    """
    Check if an email is registered on TikTok.
    
    Uses the password reset flow to probe email existence.
    Returns: Result.taken() if email exists, Result.available() if not,
             or Result.error() on failure.
    """
    base_url = "https://www.tiktok.com"
    reset_url = f"{base_url}/auth/login_forgot_password"
    api_url = f"{base_url}/passport/web/user/password/reset/send_code/"
    
    client_headers = {"user-agent": get_random_user_agent()}
    
    try:
        async with httpx.AsyncClient(headers=client_headers, http2=True, timeout=15.0) as client:
            # First visit the page to get cookies and CSRF token
            res = await client.get(reset_url, follow_redirects=True, headers={
                "accept": "text/html,application/x-www-form-urlencoded",
                "referer": base_url
            })
            
            if res.status_code != 200:
                return Result.error(f"Failed to load page (HTTP {res.status_code})")
            
            # Extract CSRF token from cookies or page content
            csrf_token = client.cookies.get("tt_web_csrf_token")
            if not csrf_token:
                match = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', res.text)
                if match:
                    csrf_token = match.group(1)
            
            if not csrf_token:
                return Result.error("CSRF token not found (IP may be flagged)")
            
            # Prepare API request headers
            headers = {
                "x_csrf_token": csrf_token,
                "x_tt_web_unique_id": client.cookies.get("tt_webid") or "",
                "accept": "application/json, text/plain, */*",
                "referer": reset_url,
                "content-type": "application/json"
            }
            
            # Send password reset code request
            payload = {"email": email, "account": "email"}
            
            response = await client.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("error_code") == 0:
                    # Email exists - account found
                    return Result.taken()
                elif data.get("message") == "user not found":
                    return Result.available()
                elif "captcha" in response.text.lower() or data.get("message", "").lower().contains("verification"):
                    return Result.error("CAPTCHA protection detected")
                else:
                    return Result.error(f"Unexpected response: {data.get('message', 'unknown')}")
            
            elif response.status_code == 400:
                # Check if it's "user not found"
                try:
                    data = response.json()
                    if data.get("message") == "user not found":
                        return Result.available()
                    elif "captcha" in response.text.lower():
                        return Result.error("CAPTCHA protection detected")
                except:
                    pass
                return Result.error("Bad request (400)")
            
            elif response.status_code == 403:
                return Result.error("Forbidden - IP or request blocked")
            
            elif response.status_code == 429:
                return Result.error("Rate limited (429)")
            
            else:
                return Result.error(f"HTTP {response.status_code}")
    
    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except httpx.ConnectError:
        return Result.error("Connection failed")
    except Exception as e:
        return Result.error(f"Unexpected error: {e}")


async def validate_tiktok(email: str) -> Result:
    """Public validation function for user-scanner."""
    return await _check(email)
