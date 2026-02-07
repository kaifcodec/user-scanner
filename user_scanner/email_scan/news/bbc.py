import httpx
import re
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    login_url = "https://account.bbc.com/auth/identifier/signin?realm=%2F&clientId=Account&action=register&ptrt=https%3A%2F%2Fwww.bbc.com%2F&userOrigin=BBCS_BBC&purpose=free"
    check_url = "https://account.bbc.com/auth/identifier/check"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Origin': "https://account.bbc.com",
    }

    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            response = await client.get(login_url, headers=headers)

            nonce_match = re.search(r'nonce=([a-zA-Z0-9\-_]+)', str(response.url))
            if not nonce_match:
                nonce_match = re.search(r'"nonce":"([a-zA-Z0-9\-_]+)"', response.text)

                return Result.error("Unable to extract nonce, report it via GitHub issues")

            nonce = nonce_match.group(1)

            params = {
                'action': "sign-in",
                'clientId': "Account",
                'context': "international",
                'isCasso': "false",
                'journeyGroupType': "sign-in",
                'nonce': nonce,
                'ptrt': "https://www.bbc.com/",
                'purpose': "free",
                'realm': "/",
                'redirectUri': "https://session.bbc.com/session/callback?realm=/",
                'service': "IdRegisterService",
                'userOrigin': "BBCS_BBC"
            }

            payload = {"userIdentifier": email}

            check_res = await client.post(check_url, params=params, json=payload, headers=headers)
            data = check_res.json()

            if data.get("exists") is True:
                return Result.taken()
            elif data.get("exists") is False:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)

async def validate_bbc(email: str) -> Result:
    return await _check(email)
