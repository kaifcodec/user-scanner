import re
import html
import httpx
from user_scanner.core.result import Result
from user_scanner.core import orchestrator

def validate_tradingview(username: str) -> Result:
    """Validate a username on TradingView."""
    url = f"https://www.tradingview.com/u/{username}/"
    show_url = f"https://www.tradingview.com/u/{username}/"
    try:
        response = orchestrator.make_request(url, follow_redirects=True)
        response_text = response.text
        
        # Verify status code 200 AND check unique TradingView strings in the response body to prevent false positives
        if response.status_code == 200 and "tradingview" in response_text.lower() and "page not found" not in response_text.lower():
            extra = {}
            title_match = re.search(r"<title>(.*?)</title>", response_text, re.IGNORECASE)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
                # TradingView format: {Name} — Trading Ideas and Scripts — TradingView
                # or {Username} — Trading Ideas and Scripts — TradingView
                title_parts = title.split(" — ")
                if len(title_parts) > 0:
                    name = title_parts[0].strip()
                    if name.lower() != username.lower():
                        extra["name"] = name
            return Result.taken(extra=extra, url=show_url)
        elif response.status_code == 404 or "page not found" in response_text.lower():
            return Result.available(url=show_url)
        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except httpx.TimeoutException:
        return Result.skipped("Connection timed out")
    except Exception as e:
        return Result.error(e, url=show_url)
