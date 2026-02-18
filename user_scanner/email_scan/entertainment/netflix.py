import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    show_url = "https://netflix.com"
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.9",
        'Origin': "https://www.netflix.com",
        'Referer': "https://www.netflix.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            await client.get("https://www.netflix.com/in/", headers=headers)

            flwssn = client.cookies.get("flwssn")
            if not flwssn:
                return Result.error("Session token not found")

            url = "https://web.prod.cloud.netflix.com/graphql"

            graphql_headers = headers.copy()
            graphql_headers.update({
                'content-type': 'application/json',
                'x-netflix.context.operation-name': 'CLCSWebInitSignup',
                'x-netflix.request.clcs.bucket': 'high'
            })

            payload = {
                "operationName": "CLCSWebInitSignup",
                "variables": {
                    "inputUserJourneyNode": "WELCOME",
                    "locale": "en-IN",
                    "inputFields": [
                        {"name": "flwssn", "value": {"stringValue": flwssn}},
                        {"name": "email", "value": {"stringValue": email}}
                    ]
                },
                "extensions": {
                    "persistedQuery": {
                        "id": "f6e8ddc6-79fb-4ff2-8e55-893d707887a4",
                        "version": 102
                    }
                }
            }

            response = await client.post(url, headers=graphql_headers, json=payload)

            if response.status_code == 200:
                resp_text = response.text

                if "sign-up link to" in resp_text:
                    return Result.available(url=show_url)

                elif "Welcome back!" in resp_text:
                    return Result.taken(url=show_url)
                else:
                    return Result.error("Unexpected response, Try an India-based VPN or report it via GitHub issues")

            return Result.error(f"HTTP {response.status_code}")

    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(f"Unexpected exception: {e}")


async def validate_netflix(email: str) -> Result:
    return await _check(email)
