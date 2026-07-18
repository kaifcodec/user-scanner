import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://fixderma-skincare.myshopify.com/api/2025-04/graphql"
    show_url = "https://www.fixderma.com"

    payload = f'mutation {{customerCreate(input:{{email:"{email}",password:"no",firstName:"nopi",lastName:"fish"}}){{customer{{firstName,lastName,email,id,tags}},customerUserErrors{{field,message}}}}}}'

    headers = {
        'User-Agent': "Mobile Buy SDK Android/2025.4.1/com.fixderma",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'x-buy3-sdk-cache-fetch-strategy': "CACHE_FIRST",
        'x-sdk-version': "2025.4.1",
        'x-sdk-variant': "android",
        'x-shopify-storefront-access-token': "7b9cc3ec1eb82866fb49d1c6d30c4981",
        'accept-language': "en",
        'content-type': "application/graphql; charset=utf-8"
    }

    async with httpx.AsyncClient(timeout=20.0, http2=True) as client:
        try:
            response = await client.post(url, content=payload, headers=headers, timeout=20.0)

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)

            if response.status_code == 200:
                data = response.json()
                errors = data.get("data", {}).get("customerCreate", {}).get("customerUserErrors", [])

                is_taken = False
                is_available = False
                extras = {}

                for error in errors:
                    msg = error.get("message", "")
                    field = error.get("field") or []
                    if "email" in field and "already been taken" in msg:
                        is_taken = True
                    elif "verify your email address" in msg:
                        is_taken = True
                        extras["status"] = "unverified"
                    elif "password" in field and "Password is too short" in msg:
                        is_available = True

                if is_taken:
                    return Result.taken(url=show_url, extra=extras)
                elif is_available:
                    return Result.available(url=show_url)

                return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

            return Result.error(f"Unexpected response status: {response.status_code}, report it via GitHub issues", url=show_url)

        except Exception as e:
            return Result.error(e, url=show_url)


async def validate_fixderma(email: str) -> Result:
    """
    Fixderma email validator. Checks Shopify storefront customerCreate mutation.
    """
    return await _check(email)
