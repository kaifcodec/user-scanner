import httpx
from httpx import ConnectError, TimeoutException

def validate_cratesio(user):
    url = f"https://crates.io/api/v1/users/{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Referer': "https://crates.io/",
        'sec-fetch-mode': "cors",
    }

    try:
        response = httpx.head(url, headers=headers, timeout=5.0)
        status = response.status_code

        if status == 200:
           return 0
        elif status == 404:
           return 1
        else:
           return 2

    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_cratesio(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
