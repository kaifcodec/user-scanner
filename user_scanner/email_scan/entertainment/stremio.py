import httpx
from secrets import token_hex
from user_scanner.core.helpers import get_global_timeout
from user_scanner.core.result import Result, Status


async def validate_stremio(email: str) -> Result:
    show_url = "https://stremio.com"
    url = "https://api.strem.io/api/login"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Origin': "https://www.stremio.com",
        'Referer': "https://www.stremio.com/",
        'Accept-Language': "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=get_global_timeout() or 15.0) as client:
            async def probe(probe_email: str) -> Result:
                response = await client.post(
                    url,
                    json={"authKey": None, "email": probe_email, "password": "wrongpassword123"},
                    headers=headers,
                )

                if response.status_code != 200:
                    return Result.error(f"HTTP {response.status_code}", url=show_url)

                data = response.json()
                error_data = data.get("error") if isinstance(data, dict) else None
                if not isinstance(error_data, dict):
                    return Result.error("Unexpected response body", url=show_url)

                wrong_pass = error_data.get("wrongPass") is True
                wrong_email = error_data.get("wrongEmail") is True
                if wrong_email and not wrong_pass:
                    return Result.available(url=show_url)
                if wrong_pass and not wrong_email:
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            result = await probe(email)
            if result.status != Status.TAKEN:
                return result

            # Stremio returned wrongPass for a generated nonexistent address.
            control = await probe(f"scanner-{token_hex(16)}@example.com")
            if control.status == Status.AVAILABLE:
                return result
            if control.status == Status.ERROR:
                return control
            return Result.error(
                "Stremio returned an unexpected response for the nonexistent-address check",
                url=show_url,
            )

    except httpx.TimeoutException:
        return Result.error("Connection timed out", url=show_url)
    except Exception as e:
        return Result.error(f"Unexpected Exception: {e}", url=show_url)
