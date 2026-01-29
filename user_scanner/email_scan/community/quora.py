import asyncio
import json
import re
import os
import shutil
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    if not shutil.which("curl"):
        return Result.error("curl is not installed, install it to use Quora validation")

    cookie_path = f"quora_cookie_{os.getpid()}.txt"
    base_url = "https://www.quora.com/"
    gql_url = "https://www.quora.com/graphql/gql_para_POST"

    headers = {
        'host': 'www.quora.com',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'referer': 'https://www.google.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    async def run_curl(url, current_headers, post_data=None, url_params=None):
        cmd = ["curl", "-s", "-k", "-L", "--http2", "--max-time",
               "5", "-c", cookie_path, "-b", cookie_path]
        for k, v in current_headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
        if url_params:
            import urllib.parse
            url += "?" + urllib.parse.urlencode(url_params)
        if post_data:
            cmd.extend(["-X", "POST", "--data-raw", json.dumps(post_data)])
        cmd.append(url)

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5)
            return stdout.decode('utf-8', errors='ignore')
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            return ""

    try:
        html = await run_curl(base_url, headers)
        if not html:
            if os.path.exists(cookie_path):
                os.remove(cookie_path)
            return Result.error("Connection timed out")

        formkey_match = re.search(r'\"formkey\":\s*\"([a-f0-9]{32})\"', html)
        if not formkey_match:
            if os.path.exists(cookie_path):
                os.remove(cookie_path)
            return Result.error("Quora blocked the request (Bot detection/403)")

        formkey = formkey_match.group(1)

        gql_headers = headers.copy()
        gql_headers.update({
            'content-type': 'application/json',
            'quora-formkey': formkey,
            'quora-canary-revision': 'false',
            'origin': 'https://www.quora.com',
            'referer': 'https://www.quora.com/',
            'priority': 'u=1, i'
        })

        payload = {
            "queryName": "SignupEmailForm_validateEmail_Query",
            "variables": {"email": email},
            "extensions": {
                "hash": "1db80096407be846d5581fe1b42b12fd05e0b40a5d3095ed40a0b4bd28f49fe7"
            }
        }

        response_text = await run_curl(gql_url, gql_headers, post_data=payload, url_params={'q': "SignupEmailForm_validateEmail_Query"})

        if os.path.exists(cookie_path):
            os.remove(cookie_path)

        if not response_text.strip():
            return Result.error("Quora timed out or returned empty body")

        data = json.loads(response_text)
        status = data.get("data", {}).get("validateEmail")

        if status == "IN_USE":
            return Result.taken()
        elif status == "OK":
            return Result.available()
        else:
            return Result.error(f"Unexpected status: {status}")

    except Exception as e:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
        return Result.error(e)


async def validate_quora(email: str) -> Result:
    return await _check(email)
