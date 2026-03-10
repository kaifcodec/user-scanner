from user_scanner.core.orchestrator import generic_validate, Result

def validate_7dach(user):
    url = f"https://7dach.ru/profile/{user}"
    show_url = url

    def process(response):
        if "Информация / Профиль" in response.text:
            return Result.taken()

        if "<title>Ошибка / 7dach.ru" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
