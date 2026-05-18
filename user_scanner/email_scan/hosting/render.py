import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.render.com/graphql"
    show_url = "https://render.com"

    payload = {
        "operationName": "validateEmail",
        "variables": {"email": email},
        "query": """
        mutation validateEmail($email: String!) {
            validateEmail(email: $email) {
                valid
                exists
            }
        }
        """
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

            if "errors" in data:
                msg = data["errors"][0].get("message", "")
                return Result.error(f"Render Error: {msg}")

            result = data.get("data", {}).get("validateEmail")

            if not result:
                return Result.error("Unexpected response format from Render")

            
            if result.get("exists"):
                return Result.taken(url=show_url)

           
            if result.get("valid"):
                return Result.available(url=show_url)

            
            return Result.error("Invalid email format")

        except Exception as e:
            return Result.error(e)


async def validate_render(email: str) -> Result:
    return await _check(email)
