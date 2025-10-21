import httpx
from httpx import ConnectError, TimeoutException

def validate_launchpad(user):
    url = f"https://launchpad.net/~{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Upgrade-Insecure-Requests': "1",
    }

    try:
        response = httpx.head(url, headers=headers, timeout=5.0, follow_redirects=True)
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
   result = validate_launchpad(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
