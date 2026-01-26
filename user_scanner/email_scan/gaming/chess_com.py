import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=True) as client:
        try:
            url = "https://www.chess.com/rpc/chesscom.authentication.v1.EmailValidationService/Validate"

            payload = {
                "email": email
            }

            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
                'Accept': "application/json, text/plain, */*",
                'Accept-Encoding': "identity",
                'Content-Type': "application/json",
                'sec-ch-ua-platform': '"Android"',
                'accept-language': "en_US",
                'connect-protocol-version': "1",
                'origin': "https://www.chess.com",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'referer': "https://www.chess.com/register",
                'priority': "u=1, i"
            }

            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                return Result.error(f"Status {response.status_code}, report is via GitHub issues")

            data = response.json()
            status = data.get("status")

            if status == "EMAIL_STATUS_TAKEN":
                return Result.taken()
            elif status == "EMAIL_STATUS_AVAILABLE":
                return Result.available()
            else:
                return Result.error(f"Unknown status: {status}, report is via GitHub issues")

        except Exception as e:
            return Result.error(f"unexpected exception: {e}")

async def validate_chess_com(email: str) -> Result:
    return await _check(email)
