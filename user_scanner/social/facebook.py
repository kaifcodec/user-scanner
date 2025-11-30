import httpx
from httpx import ConnectError, TimeoutException

def validate_facebook(username):
    url = f"https://www.facebook.com/{username}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }

    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=5)

        final_url = str(r.url).lower()

        unavailable_patterns = [
            "unsupportedbrowser",
            "help",                   # fb help redirect
            "login",                  # login without profile id
            "/people/",               # but no profile id number
            "recover",                # account recovery redirect
        ]

        # Username does NOT exist if URL ends in something not related to profile
        if any(p in final_url for p in unavailable_patterns) and "profile.php?id=" not in final_url:
            return 1  # Available

        if "profile.php?id=" in final_url:
            return 0  # Exists

        # If URL contains the username itself without redirecting to unsupported pages
        if username.lower() in final_url:
            return 0  # Exists (custom username)

        return 2

    except (ConnectError, TimeoutException):
        return 2
    except Exception:
        return 2


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_facebook(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
