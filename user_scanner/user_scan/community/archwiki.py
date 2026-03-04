from user_scanner.core.orchestrator import Result, generic_validate


def validate_archwiki(user):
    url = f"https://wiki.archlinux.org/api.php?action=query&format=json&list=users&ususers={user}&usprop=cancreate&formatversion=2"
    show_url = f"https://wiki.archlinux.org/title/User:{user}"

    def process(response):
        if '"userid":' in response.text:
            return Result.taken()
        if '"missing":true' in response.text:
            return Result.available()
        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
