import httpx
from httpx import ConnectError, TimeoutException

def validate_steam(user):
    """
    Checks if a steam username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """

    url = f"https://steamcommunity.com/id/{user}/"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
        'sec-fetch-dest': "document",
    }

    try:
        response = httpx.get(url, headers = headers, timeout = 5)

        if response.text.find("Error</title>") != -1:
            return 1
        else:
            return 0

    except (ConnectError, TimeoutException):
        return 2
    except Exception as e:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_steam(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
