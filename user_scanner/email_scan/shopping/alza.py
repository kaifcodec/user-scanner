import httpx

from user_scanner.core.result import Result, Status

ALZA_COUNTRY_CODES = ("cz", "sk", "de", "hu", "at")


async def _check_given_website(email: str, main_url: str) -> Result:
    """
    Checks whether a given email is associated with an account or order on a specified Alza regional website.

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
            return Result.taken(url=main_url, extra={"has_account": True})
        case 2:
            # Orders with this email were created, but the email does not belong to any account
            return Result.taken(url=main_url, extra={"has_account": False})
        case _:
            return Result.error(
                "Unexpected response structure, please report it via GitHub issues"
            )


async def _check(email: str) -> Result:
    """
    Check whether an email is associated with an account or order across the following Alza regional websites:

        - Czech Republic (www.alza.cz)
        - Slovakia (www.alza.sk)
        - Germany (www.alza.de)
        - Hungary (www.alza.hu)
        - Austria (www.alza.at)

    Returns:
        Result:
            - with status=TAKEN if email was found on at least one website, also returns the list of websites where the given email
                is associated with an account and a list of websites where the email was used for an order without a registered account,
            - with status=AVAILABLE if the email was not found on any of the websites,
            - with status=ERROR if an error occurred while checking any of the websites.
    """
    domain_name_template = "https://www.alza.{cctld}"
    order_only_countries = []
    account_countries = []
    for cctld in ALZA_COUNTRY_CODES:
        url = domain_name_template.format(cctld=cctld)
        result = await _check_given_website(email, url)
        if result.status == Status.TAKEN:
            if result.extra["has_account"]:
                account_countries.append(cctld)
            else:
                order_only_countries.append(cctld)
        elif result.status == Status.ERROR:
            return result

    if not account_countries and not order_only_countries:
        return Result.available()

    return Result.taken(
        extra={
            "account_countries": ", ".join(account_countries),
            "order_only_countries": ", ".join(order_only_countries),
        }
    )


async def validate_alza(email: str) -> Result:
    """
    Checks whether an email is associated with an account or order across supported Alza regional websites.
    Each regional website has its own database and users.
    """
    return await _check(email)
