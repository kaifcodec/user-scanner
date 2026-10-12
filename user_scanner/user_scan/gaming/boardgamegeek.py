from urllib.parse import quote, urljoin

import httpx

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result


def validate_boardgamegeek(user: str) -> Result:
    """Use Geekdo's shared user lookup; profile HTML is only an app shell."""
    url = "https://api.geekdo.com/api/user"
    show_url = f"https://boardgamegeek.com/profile/{quote(user, safe='')}"

    def process(response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        data = response.json()

        if not isinstance(data, list):
            return Result.error("Unexpected BoardGameGeek user response")
        if not data:
            return Result.available()
        if len(data) != 1 or not isinstance(data[0], dict):
            return Result.error("Unexpected BoardGameGeek user records")

        account = data[0]
        username = account.get("username")
        userid = account.get("userid")
        if (
            account.get("type") != "user"
            or not isinstance(username, str)
            or username.casefold() != user.casefold()
            or type(userid) is not int
            or userid <= 0
        ):
            return Result.error("Unable to verify BoardGameGeek user identity")

        extra: dict[str, str | int | list[str]] = {"user_id": userid}
        years = account.get("supportYears")
        if isinstance(years, list):
            extra["supporter_years"] = years
        for source, target in (
            ("firstname", "firstname"),
            ("lastname", "lastname"),
            ("city", "city"),
            ("state", "state"),
            ("country", "country"),
            ("regdate", "joined"),
        ):
            value = account.get(source)
            if isinstance(value, str) and value != "Unspecified":
                extra[target] = value.strip()

        credits = account.get("creditBadges")
        if isinstance(credits, dict):
            labels = []
            links = []
            for credit in credits.get("boardgame") or []:
                if not isinstance(credit, dict):
                    continue
                if isinstance(label := credit.get("label"), str):
                    labels.append(label)
                if isinstance(href := credit.get("href"), str) and href:
                    links.append(urljoin("https://boardgamegeek.com", href))
            extra["credits"] = list(dict.fromkeys(labels))
            extra["credit_links"] = list(dict.fromkeys(links))

        media = {}
        avatar = account.get("avatar")
        if isinstance(avatar, dict) and isinstance(avatar.get("urls"), dict):
            urls = avatar["urls"]
            image = urls.get("xl") or urls.get("default@2x") or urls.get("default")
            if isinstance(image, str) and image.startswith("https://"):
                media["avatar"] = image

        result = Result.taken(extra=extra, media=media)
        try:
            enrichment = make_request(f"{url}/{userid}/profile")
            if enrichment.status_code == 200:
                data = enrichment.json()
                result.update(
                    extra={
                        target: value.strip()
                        for source, target in (
                            ("body", "bio"),
                            ("shortDescription", "description"),
                            ("lastLogin", "last_seen"),
                            ("editdate", "profile_updated"),
                        )
                        if isinstance(value := data.get(source), str)
                    }
                )
        except (httpx.HTTPError, ValueError, AttributeError):
            # Optional enrichment errors must not overwrite the confirmed account.
            pass

        return result

    return generic_validate(url, process, params={"username": user}, show_url=show_url)
