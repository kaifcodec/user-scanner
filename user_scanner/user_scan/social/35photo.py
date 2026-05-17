from user_scanner.core.orchestrator import generic_validate, Result

def validate_35photo(user):
    url = f"https://35photo.pro/@{user}/"
    show_url = url

    def process(response):
        if '<span title="Total photos' in response.text:
            return Result.taken()
        
        if "Catalogs of professional author" in response.text or response.status_code == 302:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)
