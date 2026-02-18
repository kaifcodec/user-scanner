from user_scanner.core.orchestrator import status_validate
from user_scanner.core.helpers import get_random_user_agent


def validate_launchpad(user):
    url = f"https://launchpad.net/~{user}"
    show_url = "https://launchpad.net"

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Upgrade-Insecure-Requests': "1",
    }

    return status_validate(url, 404, 200, show_url=show_url, headers=headers, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_launchpad(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")