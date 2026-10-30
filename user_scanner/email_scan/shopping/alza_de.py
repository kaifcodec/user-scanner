from user_scanner.core.impersonate import impersonate_request_async
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    """
    Checks whether a given email is associated with an account or order on the Alza website.

    The check has two steps:

    1. Retrieve cookies by fetching the main page.
    2. Use the CheckLoginAvailability API endpoint. Example response:
        {
            "LoginAvailabilityType": 1,
            "DevErrorMessage": null,
            "Message": null,
            "ErrorNeoPurchaseFailed": false,
            "ErrorLevel": 0,
            "RedirectUrlOrderDetail": null,
            "PaymentAction": null,
            "CanShowFastCheckoutButton": false
        }
        The value of LoginAvailabilityType indicates whether the email is associated with a registered account (1),
        was used for an order but is not associated with an account (2), or neither (0).

        I do not know whether the other fields can have different values; they remained unchanged during testing.
    """
    main_url = "https://www.alza.de"
    check_login_availability_url = (
        f"{main_url}/Services/EShopService.svc/CheckLoginAvailability"
    )

    headers = {
        "Referer": main_url,
        "Origin": main_url,
        "Accept": "application/json",
    }

    try:
        # Fetch the main page to retrieve cookies
        response = await impersonate_request_async(
            main_url, method="GET", headers=headers, allow_redirects=True
        )

        if response.status_code != 200:
            return Result.error(
                f"Failed to access the {main_url}, HTTP {response.status_code}",
                url=main_url,
            )

        # Send post request to the API
        payload = {"login": email}
        response = await impersonate_request_async(
            check_login_availability_url,
            method="POST",
            headers=headers,
            json=payload,
        )
    except Exception as exc:
        return Result.error(exc, url=main_url)

    if response.status_code != 200:
        return Result.error(
            f"Failed to retrieve information from API, HTTP {response.status_code}",
            url=main_url,
        )

    try:
        data = response.json()
        login_availability_type = data.get("LoginAvailabilityType")
    except (ValueError, AttributeError):
        return Result.error(
            "Unexpected response structure, please report it via GitHub issues",
            url=main_url,
        )

    match login_availability_type:
        case 0:
            # Not registered, no orders with this email
            return Result.available(url=main_url)
        case 1:
            # Account with this email exists
            return Result.taken(url=main_url)
        case 2:
            # Orders with this email were created, but the email does not belong to any account
            return Result.taken(
                url=main_url,
                reason="Order was made using this email, but account does not exist.",
            )
        case _:
            return Result.error(
                "Unexpected response structure, please report it via GitHub issues",
                url=main_url,
            )


async def validate_alza_de(email: str) -> Result:
    """
    Checks whether an email is associated with an account or order on alza.de website.
    """
    return await _check(email)
