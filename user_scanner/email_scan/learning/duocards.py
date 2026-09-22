import httpx

from user_scanner.core.result import Result

QUERY = """mutation EmailAuthGetEmailInfoMutation($email: String!) {
  getEmailInfo(email: $email) {
    exists
    password
    google
    apple
    loginLinkSent
  }
}"""


async def validate_duocards(email: str) -> Result:
    """Check DuoCards login methods. May send a link to passwordless accounts."""
    show_url = "https://app.duocards.com"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.duocards.com/graphql?EmailAuthGetEmailInfoMutation",
                json={"query": QUERY, "variables": {"email": email}},
            )

            if response.status_code == 429:
                return Result.error("Rate limited", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}",
                    url=show_url,
                )

            data = response.json()
            info = data.get("data", {}).get("getEmailInfo", {})
            if info.get("exists") is True:
                extra = {
                    key: True
                    for key in ("password", "google", "apple", "loginLinkSent")
                    if info.get(key) is True
                }
                return Result.taken(extra=extra, url=show_url)
            if info.get("exists") is False:
                return Result.available(url=show_url)
            return Result.error("Unexpected response body", url=show_url)
    except (httpx.HTTPError, ValueError) as exc:
        return Result.error(exc, url=show_url)
