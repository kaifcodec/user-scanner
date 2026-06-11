import re

from user_scanner.core.orchestrator import Result, generic_validate


def validate_hackernews(user: str) -> Result:
    if not (2 <= len(user) <= 15):
        return Result.error("Length must be 2-15 characters")

    if not re.match(r"^[a-zA-Z0-9_-]+$", user):
        return Result.error("Only use letters, numbers, underscores, and hyphens")

    url = f"https://news.ycombinator.com/user?id={user}"
    show_url = f"https://news.ycombinator.com/user?id={user}"

    def process(response):
        if "No such user." in response.text:
            return Result.available()
        if f"profile: {user}" in response.text.lower() or "created:" in response.text:
            extra = {}
            html = response.text
            try:
                # Extract joined date
                created_match = re.search(r'created:</td><td><span class="age"><a[^>]+>([^<]+)</a></span></td>', html)
                if not created_match:
                    created_match = re.search(r'created:</td><td>([^<]+)</td>', html)
                if created_match:
                    extra["joined"] = created_match.group(1).strip()

                # Extract karma
                karma_match = re.search(r'karma:</td><td>([^<]+)</td>', html)
                if karma_match:
                    # Clean punctuation or extra formatting
                    karma_str = re.sub(r'[^\d]', '', karma_match.group(1))
                    if karma_str:
                        extra["karma"] = int(karma_str)

                # Extract bio / about
                about_match = re.search(r'about:</td><td[^>]*>(.*?)</td>', html, re.DOTALL)
                if about_match:
                    bio_clean = re.sub(r'<[^>]+>', '', about_match.group(1)).strip()
                    if bio_clean:
                        extra["bio"] = bio_clean
            except Exception:
                pass
            return Result.taken(extra=extra)
        return Result.error("Unexpected response structure")

    return generic_validate(
        url, process, show_url=show_url, timeout=3.0, follow_redirects=True
    )
