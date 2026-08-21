import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_d3_ru(user: str) -> Result:
    """Validate a username on D3.ru (d3.ru)."""
    url = f"https://d3.ru/user/{user}/"
    show_url = f"https://d3.ru/user/{user}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or explicit Russian not-found marker)
        if (
            response.status_code == 404
            or "ничего не найдено" in response_text_lower
            or "d3.ru — ничего не найдено" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + deep data extraction
        if response.status_code == 200 and "d3.ru" in response_text_lower:
            title_match = re.search(r"<title>d3\.ru — (.*?)</title>", response.text, re.IGNORECASE)
            if title_match:
                title_name = title_match.group(1).strip()
                if title_name and "ничего не найдено" not in title_name.lower():
                    extra = {}

                    # Extract Full Name if available and distinct
                    fullname_match = re.search(r'<h3 class="b-user_full_name">([^<]+)</h3>', response.text)
                    if fullname_match:
                        fullname = fullname_match.group(1).strip()
                        if fullname and fullname.lower() != title_name.lower():
                            extra["fullname"] = fullname
                    extra["name"] = title_name

                    # Extract Karma / Score
                    karma_match = re.search(r'class="b-karma_value">([^<]+)</span>', response.text)
                    if karma_match:
                        extra["karma"] = karma_match.group(1).strip()

                    # Extract Residence / Location
                    residence_match = re.search(r'<div class="b-user_residence">([^<]+)</div>', response.text)
                    if residence_match:
                        residence = residence_match.group(1).strip()
                        if residence:
                            extra["location"] = residence

                    # Extract Subscribers / Followers
                    subs_match = re.search(r'class="b-user_subscription_text">([^<]+)</div>', response.text)
                    if subs_match:
                        subs = subs_match.group(1).strip()
                        if subs:
                            extra["followers"] = subs

                    return Result.taken(extra=extra, url=show_url)

            return Result.error("Could not verify profile details on D3.ru", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
