import httpx
import time
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://medium.com/_/graphql"
    show_url = "https://medium.com"

    payload = {
        "operationName": "SendAccountAuthEmailMutation",
        "variables": {
            "email": email,
            "captchaValue": "",
            "operation": "login",
            "type": "LOGIN_CODE",
            "rememberMe": True
        },
        "query": "mutation SendAccountAuthEmailMutation($email: String!, $captchaValue: String, $operation: String, $type: AuthEmailFlowType!, $redirect: String, $fullName: String, $rememberMe: Boolean!) { sendAcctAuthEmail(email: $email, captchaValue: $captchaValue, operation: $operation, type: $type, redirect: $redirect, fullName: $fullName, rememberMe: $rememberMe) { __typename ... on SusiMethod { value } ... on BadRequest { message } ... on FailedChallenge { message } ... on NotFound { message } } }",
        "extensions": {
            "clientLibrary": {
                "name": "apollo-kotlin",
                "version": "4.4.1"
            }
        }
    }

    # Generate current epoch time in milliseconds for the client date header
    client_date = str(int(time.time() * 1000))

    headers = {
        'User-Agent': "donkey/4.5.1302444 (Phone; Google Pixel 6; channel:playstore; os/33)",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'x-apollo-can-be-batched': "false",
        'accept': "multipart/mixed;deferSpec=20220824, application/graphql-response+json, application/json",
        'x-obvious-cid': "android",
        'x-client-date': client_date,
        'accept-language': "en",
        'cache-control': "public, max-age=60"
    }

    async with httpx.AsyncClient(timeout=20.0, http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=20.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                auth_result = data.get("data", {}).get("sendAcctAuthEmail", {})
                typename = auth_result.get("__typename")

                if typename == "NotFound" and auth_result.get("message") == "User does not exist":
                    return Result.available(url=show_url)
                elif typename == "SusiMethod" and auth_result.get("value") == "login":
                    return Result.taken(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_medium(email: str) -> Result:
    """
    Medium email validator. Note: This will send a login code/link email if it exists.
    """
    return await _check(email)
