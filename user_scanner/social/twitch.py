import json
import re
import httpx
from user_scanner.core.orchestrator import generic_validate, Result


def validate_twitch(user: str) -> Result:
    if not (4 <= len(user) <= 25):
        return Result.error("Username must be between 4 and 25 characters long")

    if not re.match(r"^[a-zA-Z0-9]+$", user):
        return Result.error("Username can only contain alphanumeric characters (a-z, 0-9)")

    url = "https://gql.twitch.tv/gql"

    payload = [
      {
        "operationName": "ChannelLayout",
        "variables": {
          "channelLogin": user,
          "includeIsDJ": True
        },
        "extensions": {
          "persistedQuery": {
            "version": 1,
            "sha256Hash": "4c361fa1874dc8f6a49e62b56aa1032eccb31311bdb653918a924f96a8b2d1a6"
          }
        }
      }
    ]

    headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
      'Accept-Encoding': "identity",
      'Content-Type': "application/json",
      'sec-ch-ua-platform': "\"Android\"",
      'accept-language': "en-US",
      'client-id': "kimne78kx3ncx6brgo4mv6wki5h1ko",
      'client-version': "7bb0442d-1175-4ab5-9d32-b1f370536cbf",
      'origin': "https://m.twitch.tv",
      'referer': "https://m.twitch.tv/",
    }

    def process(response: httpx.Response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            return Result.error(f"Failed to decode JSON response: {e}")

        user_data = data[0].get('data', {}).get('user', {})
        typename = user_data.get('__typename')

        if typename == "User":
            return Result.taken()
        elif typename == "UserDoesNotExist":
            return Result.available()
        else:
            return Result.error("Unexpected GraphQL response structure or type.")

    return generic_validate(
        url,
        process,
        headers=headers,
        method='POST',
        content=json.dumps(payload),
        follow_redirects=False
    )


if __name__ == "__main__":
    user = input("Twitch Username?: ").strip()
    result = validate_twitch(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        reason = result.get_reason()
        print(f"Error occurred! Reason: {reason}")
