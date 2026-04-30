from user_scanner.core.orchestrator import generic_validate, Result


def validate_beatstars(user):
    url = "https://core.prod.beatstars.net/auth/graphql"
    show_url = f"https://www.beatstars.com/{user}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Accept-Language': 'en,en-US;q=0.9'
    }

    payload = {
        'operationName': 'identifierAvailable',
        'variables': {
            'identifier': f'{user}',
        },
        'query': 'query identifierAvailable($identifier: String!) {\n  identifierAvailable(identifier: $identifier) {\n    ...AccountBasicInfo\n    __typename\n  }\n}\n\nfragment AccountBasicInfo on IsIdentifierAvailableResponse {\n  available\n  profileDetails {\n    email\n    username\n    artwork {\n      url\n      fitInUrl\n      __typename\n    }\n    __typename\n  }\n  __typename\n}',
    }

    def process(response):
        if response.status_code == 200:
            data = response.json()
            available = data.get('data').get('identifierAvailable').get('available')
            if available is True:
                return Result.available()
            return Result.taken()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url, headers=headers, json=payload)
