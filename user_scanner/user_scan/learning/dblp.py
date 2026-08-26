import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_dblp(user: str) -> Result:
    """Validate an author/researcher username on DBLP (dblp.org)."""
    url = "https://dblp.org/search/author/api"
    show_url = f"https://dblp.org/search/author?q={user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + DBLP JSON response
        if response.status_code == 200 and "result" in response.text:
            try:
                data = json.loads(response.text)
                hits_data = data.get("result", {}).get("hits", {})
                total_hits = int(hits_data.get("@total", 0))

                if total_hits == 0:
                    return Result.available(url=show_url)

                hit_items = hits_data.get("hit", [])
                if isinstance(hit_items, dict):
                    hit_items = [hit_items]

                if hit_items and isinstance(hit_items, list):
                    first_hit = hit_items[0].get("info", {})
                    extra = {}

                    if author_name := first_hit.get("author"):
                        extra["author"] = str(author_name).strip()
                    if author_url := first_hit.get("url"):
                        extra["dblp_url"] = str(author_url).strip()
                    if total_hits > 1:
                        extra["total_matches"] = str(total_hits)

                    return Result.taken(extra=extra, url=show_url)
            except Exception:
                return Result.error("Failed to parse DBLP JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes or unhandled responses (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(
        url, process, headers=headers, show_url=show_url, follow_redirects=True,
        params={"q": user, "format": "json"},
    )
