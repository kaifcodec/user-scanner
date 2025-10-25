import httpx
import json
from colorama import Fore, Style
from httpx import ConnectError, TimeoutException

def validate_x(user):
    url = "https://api.twitter.com/i/users/username_available.json"

    params = {
        "username": user,
        "full_name": "John Doe",
        "email": "johndoe07@gmail.com"
    }

    headers = {
        "Authority": "api.twitter.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    try:
        response = httpx.get(url, params=params, headers=headers, timeout = 3.0)
        status = response.status_code
       # print(response.text)
        if status in [401, 403, 429]:
            return 2


        elif status == 200:
            data = response.json()
            if data.get('valid') is True:
                return 1
            elif data.get('reason') == 'taken':
                return 0
            elif (data.get('reason') == "improper_format" or data.get('reason') == "invalid_username"):
                print("\n" +"  "+f"{Fore.CYAN}X says: {data.get('desc')}{Style.RESET_ALL}")
                return 2
            else:
                return 2

    except (ConnectError, TimeoutException, json.JSONDecodeError):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_x(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
