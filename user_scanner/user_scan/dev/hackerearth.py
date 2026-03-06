from user_scanner.core.orchestrator import status_validate, Result

def validate_hackerearth(user: str) -> Result:
    url = f"https://www.hackerearth.com/@{user}"
    show_url = url

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        'Accept-Language': "en-US,en;q=0.5",
        'Upgrade-Insecure-Requests': "1",
    }

    # HackerEarth returns 404 for non-existent users and 200 for existing users.
    return status_validate(
        url,
        available=404,
        taken=200,
        show_url=show_url,
        headers=headers,
        follow_redirects=True,
        timeout=10.0
    )
