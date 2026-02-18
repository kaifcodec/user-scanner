import httpx
import json
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://cognito-idp.us-east-1.amazonaws.com"
    show_url = "https://flickr.com"

    payload = {
        "ClientId": "3ck15a1ov4f0d3o97vs3tbjb52",
        "Username": email,
        "Password": "You#are-a-n80",
        "UserAttributes": [
            {"Name": "email", "Value": email},
            {"Name": "birthdate", "Value": "1983-02-05"},
            {"Name": "given_name", "Value": "John"},
            {"Name": "family_name", "Value": "Doe"},
            {"Name": "locale", "Value": "en-us"}
        ],
        "ValidationData": [{"Name": "recaptchaToken", "Value": "Not-required"}],
        "ClientMetadata": {"referrerUrl": ""}
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        'x-amz-target': "AWSCognitoIdentityProviderService.SignUp",
        'content-type': "application/x-amz-json-1.1",
        'origin': "https://identity.flickr.com",
        'referer': "https://identity.flickr.com/sign-up"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            body = response.text

            if "An account with the given email already exists" in body:
                return Result.taken(url=show_url)
            
            elif "PreSignUp failed with error Sign Up failure" in body:
                return Result.available(url=show_url)

            return Result.error("Unexpected response body")

    except Exception as e:
        return Result.error(str(e))

async def validate_flickr(email: str) -> Result:
    return await _check(email)
