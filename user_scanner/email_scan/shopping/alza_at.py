import httpx

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
    main_url = "https://www.alza.at"
    check_login_availability_url = (
        f"{main_url}/Services/EShopService.svc/CheckLoginAvailability"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
        "Referer": main_url,
        "Origin": main_url,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # Fetch the main page to retrieve cookies
        response = await client.get(main_url, headers=headers)

        if response.status_code != 200:
            return Result.error(
                f"Failed to access the {main_url}, HTTP {response.status_code}"
            )

        # Send post request to the API
        payload = {"login": email}
        response = await client.post(
            check_login_availability_url, headers=headers, json=payload
        )

    if response.status_code != 200:
        return Result.error(
            f"Failed to retrieve information from API, HTTP {response.status_code}"
        )

    try:
        data = response.json()
        login_availability_type = data.get("LoginAvailabilityType")
    except (ValueError, AttributeError):
        return Result.error(
            "Unexpected response structure, please report it via GitHub issues"
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
                "Unexpected response structure, please report it via GitHub issues"
            )


async def validate_alza_at(email: str) -> Result:
    """
    Checks whether an email is associated with an account or order on alza.at website.
    """
    return await _check(email)
