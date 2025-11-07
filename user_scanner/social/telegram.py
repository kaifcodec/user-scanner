import httpx
import re

def validate_telegram(user: str) -> int:
    """
    Checks if a Telegram username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """
    url = f"https://t.me/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }

    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=3.0)
        if r.status_code == 200:
            return 0 if re.search(r'<div[^>]*class="tgme_page_extra"[^>]*>', r.text) else 1
        return 2
    except (httpx.ConnectError, httpx.TimeoutException):
        return 2
    except Exception:
        return 2


if __name__ == "__main__":
   user = input ("Username?: ").strip()
   result = validate_telegram(user)

   if result == 1:
      print("Available!")
   elif result == 0:
      print("Unavailable!")
   else:
      print("Error occured!")
