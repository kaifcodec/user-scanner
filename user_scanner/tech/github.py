import httpx
from httpx import ConnectError, TimeoutException

def validate_github(user):
    url = f"https://github.com/signup_check/username?value={user}"

    headers = {
          'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua-platform': "\"Linux\"",
          'sec-ch-ua': "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
          'sec-ch-ua-mobile': "?0",
          'sec-fetch-site': "same-origin",
          'sec-fetch-mode': "cors",
          'sec-fetch-dest': "empty",
          'referer': "https://github.com/signup?source=form-home-signup&user_email=",
          'accept-language': "en-US,en;q=0.9",
          'priority': "u=1, i"
}

    try:
        response = httpx.get(url, headers=headers, timeout = 3.0)
        status = response.status_code

        if status == 200:
           return 1
        elif status == 422:
           return 0
        else:
           return 2

    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_github(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
