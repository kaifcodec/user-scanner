from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_protonmail(user: str) -> Result:
    """Validate Proton Mail username availability.

    Proton exposes an availability API used by their web account app.

    - Code 12106: username exists (taken)
    - Code 1000: username does not exist (available)

    Ref: https://github.com/kaifcodec/user-scanner/issues/284
    """

    # Use the same endpoint described in the issue; keep params explicit.
    url = (
        "https://account.proton.me/api/core/v4/users/available"
        f"?Name={user}%40proton.me&ParseDomain=1"
    )
    show_url = "https://account.proton.me"

    headers = {
        # This header appears required by Proton's API.
        "x-pm-appversion": "web-mail@6.0.1.3",
        "Accept": "application/json",
    }

    def process(response):
        if response.status_code not in [200, 409]:
            return Result.error(f"[{response.status_code}] Unexpected status code from Proton")

        try:
            data = response.json()
        except Exception:
            return Result.error("Invalid JSON response from Proton")

        code = data.get("Code")
        if code == 12106:
            return Result.taken()
        if code == 1000:
            return Result.available()

        return Result.error(f"Unexpected Proton response code: {code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)
