import httpx
import asyncio

URL = "https://api.render.com/graphql"

HEADERS = {
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

EMAIL = "dimitri.acteur@outlook.com"

MUTATIONS = {
    "validateEmail": {
        "query": """
        mutation validateEmail($email: String!) {
            validateEmail(email: $email) {
                valid
                exists
            }
        }
        """,
        "variables": {"email": EMAIL}
    },

    "checkEmail": {
        "query": """
        mutation checkEmail($email: String!) {
            checkEmail(email: $email)
        }
        """,
        "variables": {"email": EMAIL}
    },

    "validateSignup": {
        "query": """
        mutation validateSignup($signup: SignupInput!) {
            validateSignup(signup: $signup)
        }
        """,
        "variables": {"signup": {"email": EMAIL}}
    },

    "signUp": {
        "query": """
        mutation signUp($signup: SignupInput!) {
            signUp(signup: $signup) {
                idToken
            }
        }
        """,
        "variables": {
            "signup": {
                "email": EMAIL,
                "password": "Test123!",
                "inviteCode": ""
            }
        }
    }
}


async def test_mutation(name, mutation):
    print(f"\n=== Testing mutation: {name} ===")

    payload = {
        "operationName": name,
        "query": mutation["query"],
        "variables": mutation["variables"]
    }

    async with httpx.AsyncClient(http2=True, timeout=5) as client:
        try:
            r = await client.post(URL, json=payload, headers=HEADERS)
            print("Status:", r.status_code)
            print("Response:", r.text)
        except Exception as e:
            print("Error:", e)


async def main():
    for name, mutation in MUTATIONS.items():
        await test_mutation(name, mutation)


if __name__ == "__main__":
    asyncio.run(main())
