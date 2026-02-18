from user_scanner.core.orchestrator import status_validate
from user_scanner.core.helpers import get_random_user_agent

def validate_instagram(user):
    url = f"https://www.threads.net/api/v1/users/web_profile_info/?username={user}"

    headers = {
        'User-Agent': get_random_user_agent(),
        'X-IG-App-ID': "936619743392459",
        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "en-US,en;q=0.9",
        'X-Requested-With': "XMLHttpRequest",
        'Referer': f"https://www.threads.net/@{user}",
    }

    return status_validate(url, 404, 200, headers=headers, http2=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_instagram(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
