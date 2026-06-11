from user_scanner.core.orchestrator import Result, generic_validate


def validate_anilist(user):
    url = "https://graphql.anilist.co"
    show_url = f"https://anilist.co/user/{user}"

    headers = {"accept": "application/json", "Content-Type": "application/json"}

    payload = {"query": 'query{User(name:"' + user + '"){id name about avatar{large} bannerImage}}'}

    def process(response):
        if response.status_code == 200 and '"id":' in response.text:
            extra = {}
            try:
                data = response.json()
                user_data = data.get("data", {}).get("User", {})
                if user_data:
                    if user_data.get("id"):
                        extra["id"] = user_data.get("id")
                    if user_data.get("about"):
                        # strip html tags if any in about
                        import re
                        clean_about = re.sub('<[^<]+?>', '', user_data.get("about"))
                        extra["about"] = clean_about.strip()
                    if user_data.get("avatar") and isinstance(user_data["avatar"], dict) and user_data["avatar"].get("large"):
                        extra["avatar"] = user_data["avatar"]["large"]
                    if user_data.get("bannerImage"):
                        extra["banner"] = user_data.get("bannerImage")
            except Exception:
                pass  # Gracefully ignore any parsing issues and fallback to basic taken status

            return Result.taken(extra=extra)

        if response.status_code == 404 or "Not Found" in response.text:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(
        url, process, show_url=show_url, method="POST", json=payload, headers=headers
    )

