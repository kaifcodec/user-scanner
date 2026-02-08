import httpx
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


async def _check(email: str) -> Result:
    url = "https://huggingface.co/api/check-user-email"
    params = {'email': email}
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Encoding': "identity",
        'referer': "https://huggingface.co/join",
        'priority': "u=1, i"
    }

    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=5)
            res_text = response.text
            st_code = response.status_code

            if st_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if st_code == 200:
                if "already exists" in res_text:
                    return Result.taken()

                if "This email address is available." in res_text:
                    return Result.available()

            return Result.error(f"HTTP Error: {response.status_code}, report it via GitHub issues")

        except Exception as e:
            return Result.error(e)


async def validate_huggingface(email: str) -> Result:
    return await _check(email)
