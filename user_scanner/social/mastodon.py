from user_scanner.core.orchestrator import status_validate


def validate_mastodon(user):
    url = f"https://mastodon.social/@{user}"

    return status_validate(url, 404, 200, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_mastodon(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print("Error occured!")
