from user_scanner.core.orchestrator import Result, generic_validate


def validate_codeforces(user):
    url = f"https://codeforces.com/api/user.info?handles={user}"
    show_url = f"https://codeforces.com/profile/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("status") == "OK" and data.get("result"):
                    res = data["result"][0]

                    extra = {
                        "firstName": res.get("firstName"),
                        "lastName": res.get("lastName"),
                        "country": res.get("country"),
                        "city": res.get("city"),
                        "organization": res.get("organization"),
                        "rating": res.get("rating"),
                        "maxRating": res.get("maxRating"),
                        "rank": res.get("rank"),
                        "maxRank": res.get("maxRank"),
                        "friendOfCount": res.get("friendOfCount"),
                    }

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 400 or response.status_code == 404:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    return generic_validate(url, process, show_url=show_url, headers=headers)
