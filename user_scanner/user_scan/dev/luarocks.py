import re
from typing import Any

import httpx

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_luarocks(user: str) -> Result:
    """
    Extracts:

    - github
    - twitter
    - website
    - registered
    - modules_count
    - downloads
    - modules_list (first 3)
    """

    if not re.match(r"^[A-Za-z0-9._-]+$", user):
        return Result.error(
            "Username may only contain letters, numbers, periods, underscores, and hyphens"
        )

    url = f"https://luarocks.org/modules/{user}"

    try:
        response = make_request(
            url,
            headers={
                "User-Agent": get_random_user_agent(),
            },
            http2=True,
        )

    except (httpx.ConnectError, httpx.TimeoutException) as err:
        return Result.error(
            f"Network transport error: {err}",
            url=url,
        )

    except Exception as err:
        return Result.error(
            f"System error checking LuaRocks: {err}",
            url=url,
        )

    if response.status_code == 404:
        return Result.available(url=url)

    # Many package names redirect somewhere else.
    # Treat redirects as "not a user profile".
    if response.status_code in (301, 302, 307, 308):
        return Result.available(url=url)

    if response.status_code != 200:
        return Result.error(
            f"Unexpected status code: {response.status_code}",
            url=url,
        )

    html = response.text

    extra: dict[str, Any] = {
        "github": None,
        "twitter": None,
        "website": None,
        "registered": None,
        "modules_count": 0,
        "downloads": 0,
        "modules_list": [],
    }

    #
    # GitHub
    #
    github_match = re.search(
        r'href="https://github\.com/([^"/?#]+)"',
        html,
        re.IGNORECASE,
    )

    if github_match:
        extra["github"] = github_match.group(1)

    #
    # Twitter
    #
    twitter_match = re.search(
        r'href="https://twitter\.com/([^"/?#]+)"',
        html,
        re.IGNORECASE,
    )

    if twitter_match:
        extra["twitter"] = twitter_match.group(1)

    #
    # Website
    #
    website_match = re.search(
        r'<h3>\s*Website\s*</h3>\s*<a[^>]+href="([^"]+)"',
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if website_match:
        extra["website"] = website_match.group(1)

    #
    # Registered timestamp
    #
    registered_match = re.search(
        r'<h3>\s*Registered\s*</h3>\s*<span\s+title="([^"]+)"',
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if registered_match:
        extra["registered"] = registered_match.group(1)

    #
    # Modules count
    #
    modules_match = re.search(
        r"<h3>\s*Modules\s*</h3>\s*([0-9,]+)",
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if modules_match:
        extra["modules_count"] = int(modules_match.group(1).replace(",", ""))

    #
    # Downloads
    #
    downloads_match = re.search(
        r"<h3>\s*Downloads\s*</h3>\s*([0-9,]+)",
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if downloads_match:
        extra["downloads"] = int(downloads_match.group(1).replace(",", ""))

    #
    # First 3 modules
    #
    modules = re.findall(
        r'<li class="module_row">.*?'
        r'<a href="([^"]+)" class="title">([^<]+)</a>.*?'
        r'<div class="summary">(.*?)</div>',
        html,
        re.IGNORECASE | re.DOTALL,
    )

    extra["modules_list"] = [name.strip() for _, name, _ in modules[:3]] + ["..."]

    return Result.taken(
        url=url,
        extra=extra,
    )
