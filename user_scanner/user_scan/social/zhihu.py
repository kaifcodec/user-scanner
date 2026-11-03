from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_zhihu(user: str) -> Result:
    url = f"https://api.zhihu.com/books/people/{user}/publications?offset=0&limit=5"
    show_url = f"https://www.zhihu.com/people/{user}"

    def process(response) -> Result:
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and ("data" in data or "paging" in data):
                    return Result.taken()
            except Exception:
                pass

        if response.status_code == 404:
            return Result.available()

        if response.status_code == 403 or "need_login" in response.text:
            return Result.error("Blocked by Zhihu login/bot protection.")

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
