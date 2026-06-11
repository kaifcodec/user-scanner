from user_scanner.core.orchestrator import generic_validate, Result

def validate_donation_alerts(user):
    url = f"https://www.donationalerts.com/api/v1/user/{user}/donationpagesettings"
    show_url = f"https://www.donationalerts.com/r/{user}"

    def process(response):
        if response.status_code == 200:
            extra = {}
            try:
                data = response.json().get("data", {})
                if name := data.get("name"): extra["name"] = name
                if currency := data.get("preferred_currency"): extra["currency"] = currency
                if avatar := data.get("avatar"): extra["avatar"] = avatar
            except Exception:
                pass
            return Result.taken(extra=extra)
        elif response.status_code == 202 or (response.status_code == 200 and not response.json().get("success", True)):
            return Result.available()
        return Result.error(f"Unexpected status {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
