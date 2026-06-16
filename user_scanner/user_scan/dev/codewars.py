from user_scanner.core.orchestrator import Result, generic_validate


def validate_codewars(user):
    url = f"https://www.codewars.com/api/v1/users/{user}"
    show_url = f"https://www.codewars.com/users/{user}"

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json()
                if data and data.get("id"):
                    ranks = data.get("ranks", {}).get("overall", {})

                    extra = {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "honor": data.get("honor"),
                        "clan": data.get("clan"),
                        "leaderboard_position": data.get("leaderboardPosition"),
                        "rank_name": ranks.get("name"),
                        "score": ranks.get("score"),
                    }

                    return Result.taken(extra=extra)
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    return generic_validate(url, process, show_url=show_url, headers=headers)
