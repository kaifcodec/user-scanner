import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    """
    Internal helper that performs email validation for TikTok.
    NOTE: TikTok has strong anti-bot protections and CAPTCHA systems.
    This implementation attempts to use TikTok's API endpoints, but may be blocked by CAPTCHAs.
    """
    # More comprehensive headers to mimic real browser behavior
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-GB;q=0.8,de;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.tiktok.com",
        "referer": "https://www.tiktok.com/login/phone-or-email/enter-phone",
        "sec-ch-ua": '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "x-tt-passport-csrf-token": "",  # May need to be extracted from initial page
        "x-secsdk-csrf-token": "",      # May need to be extracted from initial page
    }

    # Try to use TikTok's password reset endpoint which might reveal if an email exists
    async with httpx.AsyncClient(http2=True, headers=headers, timeout=15.0) as client:
        try:
            # First, try to access the main login page to establish session and extract tokens
            initial_response = await client.get("https://www.tiktok.com/login/phone-or-email/enter-phone")

            # Extract any CSRF or session tokens from the initial response if present
            # This is a simplified approach - in reality, we'd parse the HTML for these tokens
            cookies = dict(client.cookies)

            # Attempt to use password reset API endpoint
            password_reset_url = "https://www.tiktok.com/api/send/initialize_password_reset/"

            # Prepare the payload for the request - include any extracted tokens
            data = {
                "account_type": "EMAIL",
                "email": email,
                "recaptcha_token": "",
                "support_tick_token": "1",  # Common parameter in TikTok requests
                "language": "en"  # Common parameter
            }

            # Add any extracted session cookies to the request
            if cookies:
                for key, value in cookies.items():
                    if 'csrf' in key.lower() or 'token' in key.lower() or 'session' in key.lower():
                        client.headers[key] = value

            response = await client.post(password_reset_url, data=data)

            # Check response status and content
            if response.status_code == 429:
                return Result.error("Rate limited by TikTok")

            # Parse the response
            try:
                resp_data = response.json()

                # Strict check for is_registered flag in the email object
                # This is the most reliable indicator of whether an email is registered
                email_obj = resp_data.get("email", {})
                if "is_registered" in email_obj:
                    is_reg = email_obj["is_registered"]
                    if isinstance(is_reg, bool):
                        return Result.taken() if is_reg else Result.available()
                    elif isinstance(is_reg, str):
                        # Handle string representations of boolean
                        return Result.taken() if is_reg.lower() in ('true', '1', 'yes') else Result.available()

                # Check for captcha-related responses (strict check)
                if "captcha" in str(resp_data).lower() or resp_data.get("error_code") == 20001:
                    return Result.error("CAPTCHA protection detected - cannot validate")

                # Check for bot detection responses
                if resp_data.get("error_code") == 0 and "verify" in str(resp_data).lower():
                    # Even with error_code 0, if it contains verification info, it's likely bot-protected
                    return Result.error("Bot protection detected - cannot validate")

                # More specific error code handling
                error_code = resp_data.get("error_code")
                if error_code is not None:
                    if error_code == 0:
                        # Error code 0 without is_registered flag usually means bot detection
                        return Result.error("Possible bot detection - no reliable data returned")
                    elif error_code == 10000:  # Invalid email format
                        return Result.available()
                    elif error_code == 20001:  # Captcha required
                        return Result.error("CAPTCHA protection detected - cannot validate")
                    elif error_code == 20005:  # Too many requests
                        return Result.error("Rate limited by TikTok")
                    elif error_code == 20006:  # Likely bot detection
                        return Result.error("Bot protection detected - cannot validate")
                    else:
                        # Other error codes likely indicate the email wasn't found or other issues
                        return Result.error(f"TikTok API error: {error_code}")

                # If we have no error_code and no is_registered flag, it's likely bot-protected
                return Result.error("Response lacks required data - likely bot protection")

            except json.JSONDecodeError:
                # If response isn't JSON, check for other indicators
                response_text = response.text.lower()

                # Look for keywords that might indicate if email exists
                if "captcha" in response_text or "verify" in response_text or "challenge" in response_text:
                    return Result.error("CAPTCHA/challenge protection detected - cannot validate")
                elif "email" in response_text and ("registered" in response_text or "exists" in response_text):
                    return Result.taken()
                elif "not found" in response_text or "invalid" in response_text:
                    return Result.available()
                else:
                    # If we can't determine from response, it might be protected by CAPTCHA
                    return Result.error("Response indicates CAPTCHA protection or unknown format")

        except httpx.TimeoutException:
            return Result.error("Request timed out")
        except httpx.RequestError as e:
            return Result.error(f"Request error: {str(e)}")
        except Exception as e:
            return Result.error(f"Unexpected error: {str(e)}")

    # This return statement is added to satisfy mypy - though it should never be reached in normal execution
    return Result.error("Unexpected flow - no return condition met")


async def validate_tiktok(email: str) -> Result:
    """
    Validates if an email is registered on TikTok.

    NOTE: TikTok implements strong anti-bot measures including CAPTCHA challenges.
    This function may not work reliably due to these protections.

    Args:
        email: The email address to validate

    Returns:
        Result object indicating if email is taken, available, or error occurred
    """
    # Basic email format validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return Result.error("Invalid email format")

    return await _check(email)