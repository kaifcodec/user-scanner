from user_scanner.core.orchestrator import generic_validate, Result

def validate_hamaha(user):
    url = f"https://hamaha.net/{user}"
    show_url = url

    def process(response):
        if 'id="profile"' in response.text:
            return Result.taken()

        if 'content="HAMAHA  Биткоин форум. Торговля на бирже - ➨ Обучение Криптовалютам, Биткоин и NYSE "' in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

