import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_memory_lol(user: str) -> Result:
    """Validate historical Twitter/X handle presence on Memory.lol (memory.lol)."""
    url = f"https://api.memory.lol/v1/tw/{user}"
    show_url = f"https://memory.lol/tw/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + Memory.lol JSON response
        if response.status_code == 200 and "accounts" in response.text:
            try:
                data = json.loads(response.text)
                accounts = data.get("accounts", [])

                if not accounts or len(accounts) == 0:
                    return Result.available(url=show_url)

                account = accounts[0]
                extra = {}

                if account_id := (account.get("id_str") or account.get("id")):
                    extra["twitter_id"] = str(account_id)

                screen_names_map = account.get("screen_names", {})
                for handle_key, dates in screen_names_map.items():
                    if isinstance(dates, list) and dates:
                        extra["first_seen"] = str(dates[0])
                        if len(dates) > 1:
                            extra["last_seen"] = str(dates[-1])
                        break

                return Result.taken(extra=extra, url=show_url)
            except Exception:
                return Result.error("Failed to parse Memory.lol JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes or unhandled responses (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
