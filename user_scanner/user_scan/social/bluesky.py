from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_bluesky(user):
    handle = user if user.endswith('.bsky.social') else f"{user}.bsky.social"
    url = "https://bsky.social/xrpc/com.atproto.temp.checkHandleAvailability"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept-Encoding': "gzip",
        'atproto-accept-labelers': "did:plc:ar7c4by46qjdydhdevvrndac;redact",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://bsky.app",
        'sec-fetch-site': "cross-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://bsky.app/",
        'accept-language': "en-US,en;q=0.9",
    }

    params = {
        'handle': handle,
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            result_type = data.get('result', {}).get('$type')

            if result_type == "com.atproto.temp.checkHandleAvailability#resultAvailable":
                return Result.available()
            elif result_type == "com.atproto.temp.checkHandleAvailability#resultUnavailable":
                return Result.taken()
        elif response.status_code == 400:
            return Result.error("Username can only contain letters, numbers, hyphens (no leading/trailing)")

        return Result.error("Invalid status code!")

    return generic_validate(url, process, headers=headers, params=params, timeout=15.0)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_bluesky(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
