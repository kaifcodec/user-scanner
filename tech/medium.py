import httpx
from httpx import ConnectError, TimeoutException

def validate_medium(user):
    url = f"https://medium.com/@{user}"

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        'Accept': "text/html",
    }

    try:
        response = httpx.get(url, headers=headers, timeout=3.0)

        if response.status_code == 200:
            html_text = response.text


            username_tag = f'property="profile:username" content="{user}"'

            if username_tag in html_text:
                return 0
            else:
                return 1
        return 2

    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_medium(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
