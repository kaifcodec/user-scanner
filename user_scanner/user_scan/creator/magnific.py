from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.nextjs import parse_next_pages_data
from user_scanner.core.orchestrator import Result


def validate_magnific(user: str) -> Result:
    url = f"https://www.magnific.com/author/{user}"

    def process(response):
        if response.status_code not in (200, 404):
            return Result.error(f"Unexpected response status: {response.status_code}")

        try:
            data = parse_next_pages_data(response.text) or {}
            page = data.get("page")
            author = data["props"]["pageProps"].get("author")
        except (AttributeError, KeyError, TypeError):
            return Result.error("Invalid Magnific profile data")

        if response.status_code == 404:
            if page == "/404":
                return Result.available()
            return Result.error("Unexpected Magnific not-found response")

        if (
            page != "/author/[authorSlug]"
            or not isinstance(author, dict)
            or not author.get("id")
        ):
            return Result.error("Unexpected Magnific profile response")

        extra = {
            "author_id": author.get("id"),
            "slug": author.get("slug"),
            "name": author.get("name"),
            "followers": author.get("followers"),
        }

        extra.update(author.get("links") or {})

        totals = author.get("totals")
        if isinstance(totals, dict):
            for name, values in totals.items():
                if isinstance(values, dict):
                    prefix = "" if name == "assets" else f"{name}_"
                    extra[f"{prefix}assets"] = values.get("items")
                    extra[f"{prefix}downloads"] = values.get("downloads")

        return Result.taken(extra=extra, media={"avatar": author.get("avatar")})

    return impersonate_validate(url, process, allow_redirects=True)
