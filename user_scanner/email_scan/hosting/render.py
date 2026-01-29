import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://api.render.com/graphql"
    
    payload = {
        "operationName": "signUp",
        "variables": {
            "signup": {
                "email": email,
                "githubId": "",
                "name": "",
                "githubToken": "",
                "googleId": "",
                "gitlabId": "",
                "bitbucketId": "",
                "inviteCode": "",
                "password": "StandardPassword123!",
                "newsletterOptIn": False,
                "next": ""
            }
        },
        "query": "mutation signUp($signup: SignupInput!) {\n  signUp(signup: $signup) {\n    idToken\n    __typename\n  }\n}\n"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "origin": "https://dashboard.render.com",
        "referer": "https://dashboard.render.com/register",
        "accept-language": "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(http2=True, timeout=4.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited, use '-d' flag to avoid bot detection")

            data = response.json()
            errors = data.get("errors", [])

            if errors:
                msg = errors[0].get("message", "")
                if '"email":"exists"' in msg:
                    return Result.taken()
                elif '"hcaptcha_token":"invalid"' in msg:
                    return Result.available()
                else:
                    return Result.error(f"Render Error: {msg}")

            return Result.error("Unexpected error, report it via GitHub issues")

        except Exception as e:
            return Result.error(e)

async def validate_render(email: str) -> Result:
    return await _check(email)
