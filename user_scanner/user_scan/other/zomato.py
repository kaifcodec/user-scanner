from user_scanner.core.orchestrator import status_validate

def validate_zomato(user):
    url = f"https://www.zomato.com/{user}/reviews"
    show_url = url

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0"
    }

    return status_validate(url, 404, 200, headers=headers, show_url=show_url)
