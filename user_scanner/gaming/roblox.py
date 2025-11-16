import httpx
from httpx import ConnectError, TimeoutException

def validate_roblox(user):
    """
    Checks if a roblox username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """

    url = f"https://users.roblox.com/v1/users/search?keyword={user}&limit=10" # official api

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
        'sec-fetch-dest': "document",
    }

    try:
        response = httpx.get(url, headers = headers, timeout = 5.5, follow_redirects = True)
        status = response.status_code
        search_results = response.json() # api response

        if "errors" in search_results: # this usually triggers when timeout or ratelimit
            return 2

        for entry in search_results["data"]: # iterates through the entries in the search results
            # .lower() so casing from the API doesn't matter
            if entry["name"].lower() == user.lower(): # if a username matches the user
                return 0
        return 1

    except (ConnectError, TimeoutException):
        return 2
    except Exception as e:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_roblox(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
