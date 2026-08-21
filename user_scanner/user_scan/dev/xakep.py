import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_xakep(user: str) -> Result:
    """Validate a username on Xakep.ru (xakep.ru)."""
    url = f"https://xakep.ru/author/{user}/"
    show_url = f"https://xakep.ru/author/{user}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or explicit Russian 404 marker)
        if (
            response.status_code == 404
            or "страница не найдена" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + deep data extraction
        if response.status_code == 200 and "xakep" in response_text_lower:
            title_match = re.search(
                r"<title>(.*?)(?:&#8212;|&mdash;|—|-)\s*Хакер</title>",
                response.text,
                re.IGNORECASE,
            )
            if title_match:
                author_name = title_match.group(1).strip()
                if author_name and "страница не найдена" not in author_name.lower():
                    extra = {"name": author_name}

                    # Extract Author ID from body class
                    author_id_match = re.search(r'author-(\d+)', response.text)
                    if author_id_match:
                        extra["author_id"] = author_id_match.group(1)

                    return Result.taken(extra=extra, url=show_url)

            return Result.error("Could not verify author details on Xakep.ru", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
