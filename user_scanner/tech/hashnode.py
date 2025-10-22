import httpx
import json
from httpx import ConnectError, TimeoutException

def validate_hashnode(user):
    url = "https://hashnode.com/utility/ajax/check-username"

    payload = {
      "username": user,
      "name": "Dummy Dummy"
    }

    headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
      'Accept': "application/json",
      'Content-Type': "application/json",
      'Origin': "https://hashnode.com",
      'Referer': "https://hashnode.com/signup",
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=3.0)

        if response.status_code == 200:
            data = response.json()

            if 'status' in data:
                if data['status'] == 1:
                    return 1
                elif data['status'] == 0:
                    return 0

            return 2

        else:
           return 2

    except (ConnectError, TimeoutException):
        return 2
    except json.JSONDecodeError:
        return 2
    except Exception:
        return 2

if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_hashnode(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occurred!")
