import httpx
import json
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    async with httpx.AsyncClient(http2=False, follow_redirects=True) as client:
        try:
            get_url = "https://www.spotify.com/in-en/signup"
            get_headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'Accept-Encoding': "identity",
                'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-platform': "\"Linux\"",
                'upgrade-insecure-requests': "1",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "navigate",
                'sec-fetch-user': "?1",
                'sec-fetch-dest': "document",
                'referer': "https://www.spotify.com/us/signup",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=0, i"
            }

            await client.get(get_url, headers=get_headers)

            post_url = "https://spclient.wg.spotify.com/signup/public/v2/account/validate"

            payload = {
                "fields": [
                    {
                        "field": "FIELD_EMAIL",
                        "value": email
                    }
                ],
                "client_info": {
                    "api_key": "a1e486e2729f46d6bb368d6b2bcda326",
                    "app_version": "v2",
                    "capabilities": [1],
                    "installation_id": "3740cfb5-c76f-4ae9-9a94-f0989d7ae5a4",
                    "platform": "www",
                    "client_id": ""
                },
                "tracking": {
                    "creation_flow": "",
                    "creation_point": "https://www.spotify.com/us/signup",
                    "referrer": "",
                    "origin_vertical": "",
                    "origin_surface": ""
                }
            }

            post_headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                'Accept-Encoding': "identity",
                'Content-Type': "application/json",
                'sec-ch-ua-platform': "\"Linux\"",
                'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
                'sec-ch-ua-mobile': "?0",
                'origin': "https://www.spotify.com",
                'sec-fetch-site': "same-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://www.spotify.com/",
                'accept-language': "en-US,en;q=0.9",
                'priority': "u=1, i"
            }

            response = await client.post(post_url, content=json.dumps(payload), headers=post_headers)

            data = response.json()

            if "error" in data and "already_exists" in data["error"]:
                return Result.taken()
            elif "success" in data:
                return Result.available()

            return Result.error(f"Unexpected error [{response.status_code}], report it via GitHub issues")

        except Exception as e:
            return Result.error(f"Exception: {e}")


async def validate_spotify(email: str) -> Result:
    return await _check(email)
