import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_hackernews(user: str) -> Result:
    if not (2 <= len(user) <= 15):
        return Result.error("Length must be 2-15 characters")

    if not re.match(r'^[a-zA-Z0-9_-]+$', user):
        return Result.error("Only use letters, numbers, underscores, and hyphens")

    url = f"https://news.ycombinator.com/user?id={user}"

    def process(response):
        if "No such user." in response.text:
            return Result.available()
        if f"profile: {user}" in response.text.lower() or "created:" in response.text:
            return Result.taken()
        return Result.error("Unexpected response structure")

    return generic_validate(url, process, timeout=3.0, follow_redirects=True)


if __name__ == "__main__":
    user = input("Username?: ").strip()
    result = validate_hackernews(user)

    if result == 1:
        print("Available!")
    elif result == 0:
        print("Unavailable!")
    else:
        print(f"Error occurred! Reason: {result.get_reason()}")
