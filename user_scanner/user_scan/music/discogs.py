from user_scanner.core.orchestrator import generic_validate, Result


def validate_discogs(user):
    url = f"https://api.discogs.com/users/{user}"
    show_url = f"https://www.discogs.com/user/{user}"

    def process(response):
        if response.status_code == 200 and "\"id\":" in response.text:
            extra = {}
            try:
                data = response.json()
                if data.get("id"):
                    extra["id"] = data.get("id")
                if data.get("name"):
                    extra["name"] = data.get("name").strip()
                if data.get("location"):
                    extra["location"] = data.get("location").strip()
                if data.get("profile"):
                    extra["bio"] = data.get("profile").strip()
                if data.get("registered"):
                    extra["joined"] = data.get("registered")
                if data.get("releases_contributed") is not None:
                    extra["releases_contributed"] = data.get("releases_contributed")
                if data.get("releases_rated") is not None:
                    extra["releases_rated"] = data.get("releases_rated")
                if data.get("num_lists") is not None:
                    extra["lists"] = data.get("num_lists")
                if data.get("num_collection") is not None:
                    extra["collection_items"] = data.get("num_collection")
                if data.get("num_wantlist") is not None:
                    extra["wantlist_items"] = data.get("num_wantlist")
                if data.get("home_page"):
                    extra["website"] = data.get("home_page").strip()
                if data.get("avatar_url"):
                    extra["avatar"] = data.get("avatar_url")
            except Exception:
                pass
            return Result.taken(extra=extra)

        if response.status_code == 404 or "\"message\": \"User does not exist or may have been deleted.\"" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

