import json
from user_scanner.core.orchestrator import generic_validate, Result

def validate_500px(user):
    url = "https://api.500px.com/graphql"
    show_url = f"https://500px.com/{user}"

    graphql_query = (
        "query($username:String!){"
        "userByUsername(username:$username){"
        "id legacyId username displayName firstName lastName registeredAt "
        "userProfile{firstname lastname about country city state}"
        "socialMedia{website twitter facebook instagram}"
        "}}"
    )
    params = {
        "query": graphql_query,
        "variables": json.dumps({"username": user}),
    }

    def process(response):
        if response.status_code == 200:
            try:
                data = response.json().get('data', {})
                user_data = data.get('userByUsername')
                if user_data:
                    extra = {}
                    if user_data.get('legacyId'):
                        extra['id'] = user_data.get('legacyId')
                    if user_data.get('displayName'):
                        extra['displayName'] = user_data.get('displayName')
                    if user_data.get('registeredAt'):
                        extra['registeredAt'] = user_data.get('registeredAt')

                    profile = user_data.get('userProfile', {})
                    if profile.get('country'):
                        extra['country'] = profile.get('country')
                    if profile.get('city'):
                        extra['city'] = profile.get('city')
                    if profile.get('about'):
                        extra['about'] = profile.get('about')

                    social = user_data.get('socialMedia', {})
                    for net in ['website', 'twitter', 'facebook', 'instagram']:
                        if social.get(net):
                            extra[net] = social.get(net)

                    return Result.taken(extra=extra)
                else:
                    return Result.available()
            except Exception:
                pass
        elif response.status_code == 404:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    headers = {"Accept": "application/json"}
    return generic_validate(url, process, show_url=show_url, params=params, headers=headers)