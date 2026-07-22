import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://vimeo.com"
    async with httpx.AsyncClient(timeout=15.0, http2=True, follow_redirects=True) as client:
        try:
            headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                'Accept-Encoding': "gzip, deflate, br",
                'accept-language': "en-US,en;q=0.9",
                'sec-ch-ua-platform': '"Linux"',
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-mobile': "?0",
            }

            viewer = await client.get(
                "https://vimeo.com/_next/viewer",
                headers={**headers, 'Accept': "application/json", 'referer': "https://vimeo.com/join"},
            )
            token = viewer.json().get("xsrft") if viewer.status_code == 200 else None
            if not token:
                return Result.error("Token extraction failed, report it via GitHub issues")

            payload = {
                'email': email,
                'token': token,
                'action': "join",
                'service': "vimeo",
                'email_validation': "true",
            }
            response = await client.post(
                "https://vimeo.com/join",
                data=payload,
                headers={
                    **headers,
                    'Accept': "application/json",
                    'X-Requested-With': "XMLHttpRequest",
                    'content-type': "application/x-www-form-urlencoded",
                    'origin': "https://vimeo.com",
                    'referer': "https://vimeo.com/join",
                },
            )

            data = response.json()
            if isinstance(data, dict) and data.get("has_error_user_exists"):
                return Result.taken(url=show_url)
            elif isinstance(data, list):
                return Result.available(url=show_url)
            else:
                return Result.error("Unexpected response, report it via GitHub issues")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")


async def validate_vimeo(email: str) -> Result:
    return await _check(email)
