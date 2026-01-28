import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    """
    Internal helper that performs email validation for TikTok.
    NOTE: TikTok has strong anti-bot protections and CAPTCHA systems.
    This implementation attempts to use TikTok's API endpoints, but may be blocked by CAPTCHAs.
    """
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.tiktok.com",
        "referer": "https://www.tiktok.com/",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    # Try to use TikTok's password reset endpoint which might reveal if an email exists
    async with httpx.AsyncClient(http2=True, headers=headers, timeout=15.0) as client:
        try:
            # First, try to access the main page to establish session
            await client.get("https://www.tiktok.com/")

            # Attempt to use password reset API endpoint
            password_reset_url = "https://www.tiktok.com/api/send/initialize_password_reset/"

            # Prepare the payload for the request
            data = {
                "account_type": "EMAIL",
                "email": email,
                "recaptcha_token": ""  # TikTok requires recaptcha, which makes automated requests difficult
            }

            response = await client.post(password_reset_url, data=data)

            # Check response status and content
            if response.status_code == 429:
                return Result.error("Rate limited by TikTok")

            # Parse the response
            try:
                resp_data = response.json()

                # Check for specific indicators in the response
                if "email" in resp_data and "is_registered" in resp_data:
                    if resp_data.get("email", {}).get("is_registered", False):
                        return Result.taken()
                    else:
                        return Result.available()

                # Check for captcha-related responses
                if "captcha" in str(resp_data).lower() or resp_data.get("error_code") == 20001:
                    return Result.error("CAPTCHA protection detected - cannot validate")

                # Alternative check for error codes that indicate email existence
                if "error_code" in resp_data:
                    error_code = resp_data["error_code"]
                    # Common error codes that might indicate email exists vs doesn't exist
                    if error_code == 0:
                        # Success - might mean email exists, but could also trigger CAPTCHA
                        if "verify" in str(resp_data).lower() or "captcha" in str(resp_data).lower():
                            return Result.error("CAPTCHA protection detected - cannot validate")
                        return Result.taken()
                    elif error_code == 10000:  # Common error code for invalid email
                        return Result.available()
                    else:
                        # Some other error occurred, possibly CAPTCHA protection
                        return Result.error(f"TikTok API error: {error_code}. Likely CAPTCHA protected.")

            except json.JSONDecodeError:
                # If response isn't JSON, check for other indicators
                response_text = response.text.lower()

                # Look for keywords that might indicate if email exists
                if "captcha" in response_text or "verify" in response_text:
                    return Result.error("CAPTCHA protection detected - cannot validate")
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

    # This return statement is added to satisfy mypy - though it should never be reached
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