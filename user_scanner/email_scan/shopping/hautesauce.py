import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.buyhautesauce.com/api/2024-04/graphql.json"
    show_url = "https://www.buyhautesauce.com"

    payload = {
        "query": "mutation customerCreate($input: CustomerCreateInput!) {\n  customerCreate(input: $input) {\n    customer {\n      id\n      firstName\n      lastName\n      acceptsMarketing\n      email\n    }\n    customerUserErrors {\n      field\n      message\n      code\n    }\n  }\n}",
        "operationName": "customerCreate",
        "variables": {
            "input": {
                "acceptsMarketing": False,
                "email": email,
                "password": "",
                "firstName": "Lost",
                "lastName": "Knight"
            }
        }
    }

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept': "application/graphql+json, application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'x-shopify-storefront-access-token': "7b89272b5ed5a3ff00ad881bf63b130a"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=6.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                errors = data.get("data", {}).get("customerCreate", {}).get("customerUserErrors", [])

                is_taken = False
                is_available = False
                extras = {}

                for error in errors:
                    code = error.get("code", "")
                    msg = error.get("message", "")
                    field = error.get("field") or []

                    if code == "TAKEN" or "already been taken" in msg or "already exists" in msg:
                        is_taken = True
                    elif "verify your email address" in msg:
                        is_taken = True
                        extras["is_verified"] = "False"
                    elif code == "BLANK" or "Password" in msg or "password" in field:
                        is_available = True

                if is_taken:
                    return Result.taken(url=show_url, extra=extras)
                elif is_available:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_hautesauce(email: str) -> Result:
    """
    Haute Sauce email validator. Checks Shopify storefront customerCreate mutation.
    """
    return await _check(email)
