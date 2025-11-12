import httpx
from httpx import ConnectError, TimeoutException

def validate_discord(user):
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"

    headers = {
        "authority": "discord.com",
        "accept": "/",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://discord.com",
        "referer": "https://discord.com/register"
    }
    
    data = {"username": user}
    
    try:
        response = httpx.post(url, headers=headers, json=data, timeout=3.0)
        if response.status_code == 200:
            status = response.json().get("taken")
            if status is True:
                return 0
            elif status is False:
                return 1
        return 2
    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_discord(user)
   
   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")



