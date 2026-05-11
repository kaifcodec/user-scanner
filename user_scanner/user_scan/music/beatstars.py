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
        try:
            res_json = response.json()

            if "errors" in res_json and res_json["errors"]:
                raw_err = res_json["errors"][0].get("message", "")

                if "ITEM_NOT_FOUND" in raw_err:
                    return Result.available("Username too short or invalid length")

                if "valid email or username" in raw_err:
                    return Result.available("Invalid username format")

                return Result.error(f"API Error: {raw_err}")

            data = res_json.get("data", {})
            identifier_data = data.get("identifierAvailable")

            if not identifier_data:
                return Result.error("Could not parse identifier data")

            if identifier_data.get("available") is True:
                return Result.available()

            return Result.taken()

        except (AttributeError, ValueError, KeyError):
            return Result.error("Failed to decode server response, report it via GitHub issues")

    return generic_validate(url, process, show_url=show_url, method="POST", headers=headers, json=payload)
