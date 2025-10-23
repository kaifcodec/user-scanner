import httpx
from httpx import ConnectError, TimeoutException

def validate_snapchat(user):
    url = f"https://www.snapchat.com/@{user}"

    headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
      'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
      'Accept-Encoding': "gzip, deflate, br, zstd",
      'sec-ch-ua': "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
      'sec-ch-ua-mobile': "?1",
      'sec-ch-ua-platform': "\"Android\"",
      'upgrade-insecure-requests': "1",
      'sec-fetch-site': "none",
      'sec-fetch-mode': "navigate",
      'sec-fetch-user': "?1",
      'sec-fetch-dest': "document",
      'accept-language': "en-US,en;q=0.9",
      'priority': "u=0, i"
    }

    try:
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout = 3.0)
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
   result = validate_snapchat(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
