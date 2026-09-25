from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_zillow(user: str) -> Result:
    """
    Validate Zillow username availability by checking the profile page.
    Uses refined headers and final URL validation to bypass anti-bot measures.
    """
    url = f"https://www.zillow.com/profile/{user}/"
    show_url = "https://www.zillow.com"

    # Refined headers that worked in testing to bypass 403 Forbidden
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Ch-Ua": '"Not(A:Bar";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    def process(response):
        # Check for redirects to general professionals pages (indicates profile not found)
        final_url = str(response.url).lower()
        if "/professionals/" in final_url or "real-estate-agent-reviews" in final_url:
            return Result.available()

        if response.status_code == 200:
            # Confirm we are still on a profile-like path
            if f"/profile/{user}".lower() in final_url:
                # Check for profile markers in the body as suggested in Issue #292
                text = response.text
                if any(marker in text for marker in ["Real Estate Agent", "Reviews", "Profile", "window.__NEXT_DATA__"]):
                    return Result.taken()
            
            return Result.available()

        if response.status_code == 404:
            return Result.available()

        if response.status_code == 403:
             return Result.error("Access denied by Zillow (PerimeterX block)")

        return Result.error(f"Unexpected status code: {response.status_code}")

    # Pass http2=True as it's often more reliable for bypassing bot detection
    return generic_validate(url, process, headers=headers, show_url=show_url, http2=True, follow_redirects=True)
