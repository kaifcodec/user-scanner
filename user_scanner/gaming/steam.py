from user_scanner.core.orchestrator import generic_validate


def validate_steam(user):
    """
    Checks if a steam username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """

    url = f"https://steamcommunity.com/id/{user}/"

    def process(response):
        if response.status_code == 200:
            if response.text.find("Error</title>") != -1:
                return 1
            else:
                return 0
        return 2

    return generic_validate(url, process)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_steam(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
