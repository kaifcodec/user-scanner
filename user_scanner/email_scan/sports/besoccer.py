import httpx
import random
from user_scanner.core.result import Result

def _generate_unique_username(base_user: str = "scanner_user") -> str:
    """Appends a large random integer to make sure the username doesn't trip error_code 1."""
    return f"{base_user}_{random.randint(1000000, 9999999)}"

async def _check(email: str) -> Result:
    url = "https://fast.okcats.com/scripts/api/api.php"
    show_url = "https://www.besoccer.com/"

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept-Encoding': "gzip"
    }

    params = {
        'key': "b3fcd6725e03f4e5d588f6624cac5522",
        'format': "json",
        'site': "ResultadosAndroid",
        'appCountry': "",
        'lang': "en-US",
        'req': "register",
        'device': "android",
        'user': _generate_unique_username(),  # Isolates the email error condition
        'email': email,
        'password': ""  # Kept empty to trigger the expected response error blocks
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return Result.error("Access forbidden by security perimeter (403)")
            if response.status_code != 200:
                return Result.error(f"Target API responded with HTTP status {response.status_code}")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to decode response signature as JSON payload")

            # Extract the errors list block safely
            errors_list = data.get("errors", [])
            if not isinstance(errors_list, list):
                return Result.error("Unexpected schema structure for 'errors' element")

            error_messages = {
                item.get("message")
                for item in errors_list
                if isinstance(item, dict)
            }

            if "Email is already in use" in error_messages:
                return Result.taken(url=show_url)

            if (
                "You must introduce a valid email address" in error_messages
                or "You must introduce a password" in error_messages
            ):
                return Result.available(url=show_url)

            return Result.error("Ambiguous error matrix returned from target endpoint")

    except Exception as e:
        return Result.error(str(e))

async def validate_okcats(email: str) -> Result:
    return await _check(email)
