from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_roblox(user):
    # official api
    url = f"https://users.roblox.com/v1/users/search?keyword={user}&limit=10"

    def process(response):
        search_results = response.json()  # api response

        if response.status_code == 429:
            return Result.error("Too many requests")

        if response.status_code == 400:
            error = search_results["errors"][0] #Api states theres always an error
            if error["code"] == 6:
                return Result.error("Username is too short")
            if error["code"] == 5:
                return Result.error("Username was filtered")
            #Shouldn't be able to reach this
            return Result.error("Invalid username")

        # iterates through the entries in the search results
        for entry in search_results["data"]:
            # .lower() so casing from the API doesn't matter
            if entry["name"].lower() == user.lower():  # if a username matches the user
                return Result.taken()
        return Result.available()

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
