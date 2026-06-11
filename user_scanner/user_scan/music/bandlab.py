from user_scanner.core.orchestrator import generic_validate, Result


def validate_bandlab(user):
    url = f"https://www.bandlab.com/api/v1.3/users/{user}"
    show_url = f"https://www.bandlab.com/{user}"

    def process(response):
        if response.status_code == 200 and "about" in response.text:
            extra = {}
            try:
                data = response.json()
                if data.get("id"):
                    extra["id"] = data.get("id")
                if data.get("name"):
                    extra["name"] = data.get("name").strip()
                if data.get("about"):
                    extra["bio"] = data.get("about").strip()
                if data.get("place"):
                    extra["location"] = data.get("place")
                if data.get("createdOn"):
                    extra["joined"] = data.get("createdOn")
                counters = data.get("counters", {})
                if counters:
                    if counters.get("followers") is not None:
                        extra["followers"] = counters.get("followers")
                    if counters.get("following") is not None:
                        extra["following"] = counters.get("following")
                    if counters.get("plays") is not None:
                        extra["plays"] = counters.get("plays")
                    if counters.get("bands") is not None:
                        extra["bands"] = counters.get("bands")
                if data.get("picture") and isinstance(data["picture"], dict) and data["picture"].get("url"):
                    extra["avatar"] = data["picture"]["url"]
            except Exception:
                pass
            return Result.taken(extra=extra)

        if response.status_code == 404 or "Couldn't find any matching element" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

