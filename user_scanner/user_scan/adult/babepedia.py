import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_babepedia(user):
    url = f"https://www.babepedia.com/user/{user}"
    show_url = f"https://www.babepedia.com/user/{user}"

    def process(response):
        if response.status_code == 200 and "'s Profile</title>" in response.text:
            extra = {}

            # Extract standard account info fields from the Profile Page table
            status_match = re.search(
                r"Account status:.*?<span[^>]*>(.*?)</span>", response.text, re.DOTALL | re.IGNORECASE)
            if status_match:
                extra["status"] = status_match.group(1).strip()

            signup_match = re.search(
                r"Signed up on:.*?<td>(.*?)</td>", response.text, re.DOTALL | re.IGNORECASE)
            if signup_match:
                extra["signup_date"] = signup_match.group(1).strip()

            seen_match = re.search(
                r"Last seen on:.*?<td>(.*?)</td>", response.text, re.DOTALL | re.IGNORECASE)
            if seen_match:
                extra["last_seen"] = seen_match.group(1).strip()

            logins_match = re.search(
                r"Logins:.*?<td>(.*?)</td>", response.text, re.DOTALL | re.IGNORECASE)
            if logins_match:
                extra["logins"] = logins_match.group(1).strip()

            views_match = re.search(
                r"Views of this page:.*?<td>(.*?)</td>", response.text, re.DOTALL | re.IGNORECASE)
            if views_match:
                extra["views"] = views_match.group(1).strip()

            return Result.taken(extra=extra, url=show_url)

        if response.status_code == 404 or "Profile not found" in response.text:
            return Result.available(url=show_url)

        return Result.error("Unexpected response body, report it via GitHub issues", url=show_url)

    return generic_validate(url, process, show_url=show_url)
