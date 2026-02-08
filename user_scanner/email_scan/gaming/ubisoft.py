import httpx
import json
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://public-ubiservices.ubi.com/v3/users/validatecreation"

    payload = {
        "email": email,
        "confirmedEmail": email,
        "firstName": "Silent",
        "lastName": "Robot",
        "nameOnPlatform": "no3motions_l3ft_but",
        "legalOptinsKey": "",
        "isDateOfBirthApprox": False,
        "age": None,
        "dateOfBirth": "2000-12-12T00:00:00.000Z",
        "password": "Never_Want3d@to",
        "country": "US",
        "preferredLanguage": "en"
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'ubi-appid': "aa88e512-9395-457d-bcb9-8d59c23f88c9",
        'sec-ch-ua-platform': "\"Android\"",
        'ubi-requestedplatformtype': "uplay",
        'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://connect.ubisoft.com",
        'sec-fetch-site': "cross-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://connect.ubisoft.com/",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"

    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)
            body = response.text

            if "Invalid email" in body:
                return Result.taken()

            if "legalOptinsKey" in body and "Invalid email" not in body:
                return Result.available()

            return Result.error("Unexpected response body, report it on github")

    except Exception as e:
        return Result.error(e)


async def validate_ubisoft(email: str) -> Result:
    return await _check(email)
