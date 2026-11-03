from user_scanner.core.orchestrator import generic_validate, Result


def validate_minds(user: str) -> Result:
    url = "https://www.minds.com/api/v3/register/validate"
    show_url = f"https://www.minds.com/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get("status") == "success":
                    if data.get("valid") is False:
                        return Result.taken()
                    if data.get("valid") is True:
                        return Result.available()
            except Exception:
                pass

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, params={"username": user})
