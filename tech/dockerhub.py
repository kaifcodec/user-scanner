import httpx
from httpx import ConnectError, TimeoutException

def validate_dockerhub(user):
    url = f"https://hub.docker.com/v2/users/{user}/"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "application/json",
    }

    try:
        response = httpx.get(url, headers=headers, timeout=3.0)
        status = response.status_code

        # UNAVAILABLE (return 0) if the user API endpoint returns 200 OK
        if status == 200:
           return 0
        # AVAILABLE (return 1) if the user API endpoint returns 404 Not Found
        elif status == 404:
           return 1
        # Other status codes are errors
        else:
           return 2

    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_dockerhub(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
