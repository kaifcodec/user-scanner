from user_scanner.core.orchestrator import generic_validate, Result


def validate_discogs(user: str) -> Result:
    url = f"https://api.discogs.com/users/{user}"
    show_url = f"https://www.discogs.com/user/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            extra: dict = {}
            media: dict = {}

            try:
                data = response.json()
                if isinstance(data, dict) and ("username" in data or "id" in data):
                    if data.get("id"):
                        extra["id"] = data["id"]
                    if data.get("name"):
                        extra["name"] = str(data["name"]).strip()
                    if data.get("location"):
                        extra["location"] = str(data["location"]).strip()
                    if data.get("profile"):
                        extra["bio"] = str(data["profile"]).strip()
                    if data.get("registered"):
                        extra["joined"] = data["registered"]
                    if data.get("rank") is not None:
                        extra["rank"] = data["rank"]
                    if data.get("buyer_rating") is not None:
                        extra["buyer_rating"] = data["buyer_rating"]
                    if data.get("seller_rating") is not None:
                        extra["seller_rating"] = data["seller_rating"]
                    if data.get("releases_contributed") is not None:
                        extra["releases_contributed"] = data["releases_contributed"]
                    if data.get("releases_rated") is not None:
                        extra["releases_rated"] = data["releases_rated"]
                    if data.get("num_lists") is not None:
                        extra["lists"] = data["num_lists"]
                    if data.get("num_collection") is not None:
                        extra["collection_items"] = data["num_collection"]
                    if data.get("num_wantlist") is not None:
                        extra["wantlist_items"] = data["num_wantlist"]
                    if data.get("home_page"):
                        extra["website"] = str(data["home_page"]).strip()
                    if data.get("avatar_url"):
                        media["avatar"] = str(data["avatar_url"])
                    return Result.taken(extra=extra, media=media)
            except Exception:
                pass

        if response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
