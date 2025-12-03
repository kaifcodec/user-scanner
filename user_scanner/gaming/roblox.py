from user_scanner.core.orchestrator import generic_validate


def validate_roblox(user):
    """
    Checks if a roblox username is available.
    Returns: 1 -> available, 0 -> taken, 2 -> error
    """

    # official api
    url = f"https://users.roblox.com/v1/users/search?keyword={user}&limit=10"

    def process(response):
        search_results = response.json()  # api response

        if "errors" in search_results:  # this usually triggers when timeout or ratelimit
            return 2

        # iterates through the entries in the search results
        for entry in search_results["data"]:
            # .lower() so casing from the API doesn't matter
            if entry["name"].lower() == user.lower():  # if a username matches the user
                return 0
        return 1

    return generic_validate(url, process, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_roblox(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occurred!")
