import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_fragment(user: str) -> Result:
    """Validate a username on Fragment (fragment.com)."""
    url = f"https://fragment.com/username/{user}"
    show_url = f"https://fragment.com/username/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or generic fallback title)
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
        page_title = title_match.group(1).strip() if title_match else ""

        if response.status_code == 404 or (
            response.status_code == 200 and page_title.lower() == "fragment" and "tm-section-header-status" not in response.text
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + data extraction
        if response.status_code == 200 and "fragment" in response_text_lower:
            if user.lower() in page_title.lower() or "tm-section-header-status" in response.text or "tm-value" in response.text:
                extra = {"username": user}

                status_match = re.search(r'<div class="tm-section-header-status[^"]*">([^<]+)</div>', response.text)
                if status_match:
                    extra["status"] = status_match.group(1).strip()

                price_match = re.search(r'<div class="table-cell-value tm-value[^>]*>([^<]+)</div>', response.text)
                if price_match:
                    price_val = price_match.group(1).strip()
                    if price_val and not price_val.startswith("@"):
                        extra["price_ton"] = price_val

                return Result.taken(extra=extra, url=show_url)

            return Result.error("Could not verify username details on Fragment", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
