from user_scanner.core.orchestrator import status_validate

def validate_donation_alerts(user):
    url = f"https://www.donationalerts.com/api/v1/user/{user}/donationpagesettings"
    show_url = f"https://www.donationalerts.com/r/{user}"

    return status_validate(url, 202, 200, show_url=show_url)
