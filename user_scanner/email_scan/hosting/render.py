import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://api.render.com/graphql"
    show_url = "https://render.com"

    payload = {
        "operationName": "signUp",
        "variables": {
            "signup": {
                "email": email,
                "password": "Test123!",
                "inviteCode": ""
            }
        },
        "query": """
        mutation signUp($signup: SignupInput!) {
            signUp(signup: $signup) {
                idToken
            }
        }
        """
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "origin": "https://dashboard.render.com",
        "referer": "https://dashboard.render.com/register",

        # Headers internes obligatoires
        "x-render-client-name": "dashboard",
        "x-render-client-version": "1.0.0",
        "x-render-client-platform": "web",
        "x-render-client-build": "production",
        "x-render-client-release-channel": "stable"
    }

    async with httpx.AsyncClient(http2=True, timeout=5) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            # Render renvoie toujours une erreur dans "errors"
            if "errors" in data:
                raw = data["errors"][0]["message"]

                # Le message est un JSON encodé dans une string
                try:
                    msg = json.loads(raw)
                except Exception:
                    return Result.error(f"Render Error: {raw}")

                # 1) Compte Render classique
                if msg.get("email") == "exists":
                    return Result.taken(url=show_url)

                # 2) Compte OAuth (GitHub / Google)
                if msg.get("email") == "invalid":
                    return Result.taken(url=show_url)

                # 3) Email valide mais non existant
                if msg.get("hcaptcha_token") == "invalid":
                    return Result.available(url=show_url)

                return Result.error(f"Render Error: {msg}")

            return Result.error("Unexpected response format from Render")

        except Exception as e:
            return Result.error(e)


async def validate_render(email: str) -> Result:
    return await _check(email)
