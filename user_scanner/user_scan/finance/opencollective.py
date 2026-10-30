import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_opencollective(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    api_url = f"https://opencollective.com/{encoded_user}.json"
    show_url = f"https://opencollective.com/{encoded_user}"

    def process(response) -> Result:
        status = response.status_code

        if status in (404, 410) and "Not found" in response.text:
            return Result.available(url=show_url)

        if status == 200:
            try:
                data = response.json()
                slug = data.get("slug")
                if isinstance(slug, str) and slug.lower() == user.lower():
                    extra: dict[str, str | int] = {"slug": slug}
                    media: dict[str, str] = {}

                    if currency := data.get("currency"):
                        extra["currency"] = str(currency)
                    if (balance := data.get("balance")) is not None:
                        extra["balance"] = balance
                    if (yearly := data.get("yearlyIncome")) is not None:
                        extra["yearly_income"] = yearly
                    if (backers := data.get("backersCount")) is not None:
                        extra["backers_count"] = backers
                    if image := data.get("image"):
                        media["avatar"] = str(image)

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("Unexpected OpenCollective response format", url=show_url)

        return Result.error(f"Unexpected response status {status}", url=show_url)

    return impersonate_validate(
        api_url,
        process,
        show_url=show_url,
        allow_redirects=True,
    )
