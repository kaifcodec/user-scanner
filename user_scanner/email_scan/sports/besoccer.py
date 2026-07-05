import httpx
import random
from user_scanner.core.result import Result

def _generate_unique_username(base_user: str = "scanner_user") -> str:
    """Appends a large random integer to make sure the username doesn't trip error_code 1."""
    return f"{base_user}_{random.randint(10000000, 99999999)}"

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

            # Compile all error codes returned in this transaction flight
            error_codes = {item.get("error_code") for item in errors_list if isinstance(item, dict)}

            # error_code 2 means the email is tied to an existing database record
            if 2 in error_codes:
                return Result.taken(url=show_url)

            # If error_code 3 is present but error_code 2 is NOT, the email is completely clear/available!
            if 3 in error_codes:
                return Result.available(url=show_url)

            return Result.error("Ambiguous error matrix returned from target endpoint")

    except Exception as e:
        return Result.error(str(e))

async def validate_okcats(email: str) -> Result:
    return await _check(email)
