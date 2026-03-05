from user_scanner.core.orchestrator import Result, generic_validate


def validate_anilist(user):
    url = "https://graphql.anilist.co"
    show_url = f"https://anilist.co/user/{user}"

    headers = {"accept": "application/json", "Content-Type": "application/json"}

    payload = {"query": 'query{User(name:"' + user + '"){id name}}'}

    def process(response):
        if response.status_code == 200 and '"id":' in response.text:
            return Result.taken()

        if response.status_code == 404 or "Not Found" in response.text:
            return Result.available()

        return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(
        url, process, show_url=show_url, method="POST", json=payload, headers=headers
    )
