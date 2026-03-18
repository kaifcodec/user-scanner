from user_scanner.core.orchestrator import generic_validate, Result

def validate_zmarsa(user):
    url = f"https://zmarsa.com/uzytkownik/{user}"
    show_url = url

    def process(response):
        if "Statystyki" in response.text:
            return Result.taken()

        if "<title>Error 404 - zMarsa.com<" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
