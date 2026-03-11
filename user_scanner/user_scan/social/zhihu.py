from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_zhihu(user):
    url = f"https://api.zhihu.com/books/people/{user}/publications?offset=0&limit=5"
    show_url = f"https://www.zhihu.com/people/{user}"

    def process(response):
        if response.status_code == 200 and "is_start" in response.text:
            return Result.taken()
        if "NotFoundException" in response.text or response.status_code == 404:
            return Result.available()
        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
