import httpx
from httpx import ConnectError, TimeoutException

def validate_instagram(user):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        'X-IG-App-ID': "936619743392459",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
        'X-Requested-With': "XMLHttpRequest",
        'Referer': f"https://www.instagram.com/{user}/",
    }

    try:
        response = httpx.get(url, headers=headers, timeout = 3.0)
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
   result = validate_instagram(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
