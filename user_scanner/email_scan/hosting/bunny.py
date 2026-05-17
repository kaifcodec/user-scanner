import httpx
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://api.bunny.net/auth/register"
    show_url = "https://dash.bunny.net/"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Brave";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': "?1",
        'sec-gpc': "1",
        'accept-language': "en-US,en;q=0.9",
        'origin': "https://dash.bunny.net",
        'sec-fetch-site': "same-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': show_url,
        'priority': "u=1, i"
    }

    # Static tokens preserved since they skip backend verification for this check
    payload = {
        "AffiliateCode": "9sa3wl8vst",
        "PowToken": "39bbb876b0e4f380:e80448fecdf5d1a40fcabf2e20d79c",
        "Email": email,
        "Password": "th3_knight_n3v3r_had_th3_st33l_h3rt_it_was_an_arm0r",  # Kept as is to trigger the field errors
        "Utm": {
            "pk_buttonlocation": "menu",
            "ref_domain": "https://www.saashub.com/"
        }
    }

    try:
        # Enforcing http2=True to prevent protocol/handshake drops
        async with httpx.AsyncClient(timeout=6.0, http2=True) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF/Mitigation (403)")
            if response.status_code == 429:
                return Result.error("Rate limited (429)")

            try:
                data = response.json()
            except Exception:
                return Result.error("Failed to parse JSON response")

            msg = data.get("Message", "")
            field = data.get("Field", "")

            if "already in use" in msg.lower() or field.lower() == "email":
                return Result.taken(url=show_url)

            if "passwords must have" in msg.lower():
                return Result.available(url=show_url)

            return Result.error(f"Unexpected response structure: {msg[:50]}")

    except httpx.RemoteProtocolError:
        return Result.error("HTTP/2 Protocol Error occurred during stream")
    except Exception as e:
        return Result.error(str(e))

async def validate_bunny(email: str) -> Result:
    return await _check(email)

