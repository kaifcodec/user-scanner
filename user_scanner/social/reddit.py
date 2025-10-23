import httpx
from httpx import ConnectError, TimeoutException

def validate_reddit(user):
    url = f"https://www.reddit.com/user/{user}/"

    headers = {
      'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
      'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      'Accept-Encoding': "gzip, deflate, br",
      'Accept-Language': "en-US,en;q=0.9",
      'sec-fetch-dest': "document",
    }

    NOT_FOUND_STRING = "Sorry, nobody on Reddit goes by that name."

    try:
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout = 3.0)

        if response.status_code == 200:
            if NOT_FOUND_STRING in response.text:
                return 1
            else:
                return 0
        else:
           return 2

    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_reddit(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
