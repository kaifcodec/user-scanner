import json
import re

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_flickr(user: str) -> Result:
    url = f"https://www.flickr.com/photos/{user}/"
    headers = {
        "User-Agent": get_random_user_agent()
    }

    try:
        response = make_request(url, headers=headers)
        if response.status_code == 404:
            return Result.available(url=url)

        if response.status_code == 200:
            extra = {}
            # extract modelExport JSON
            match = re.search(r"modelExport:(.*),[\s\S]*auth", response.text)
            if match:
                try:
                    json_str = match.group(1).replace(
                        '%20', ' ').replace('%2C', ',')
                    data = json.loads(json_str)

                    def find_model(d, registry_name):
                        if isinstance(d, dict):
                            if d.get('_flickrModelRegistry') == registry_name:
                                return d
                            for k, v in d.items():
                                res = find_model(v, registry_name)
                                if res:
                                    return res
                        elif isinstance(d, list):
                            for i in d:
                                res = find_model(i, registry_name)
                                if res:
                                    return res
                        return None

                    person_model = find_model(data, 'person-models')
                    if person_model:
                        if person_model.get('id'):
                            extra['flickr_id'] = person_model['id']
                        if person_model.get('pathAlias'):
                            extra['flickr_username'] = person_model['pathAlias']
                        if person_model.get('username'):
                            extra['flickr_nickname'] = person_model['username']
                        if person_model.get('realname'):
                            extra['fullname'] = person_model['realname']
                        buddyicon = person_model.get('buddyicon', {})
                        if isinstance(buddyicon, dict) and buddyicon.get('data', {}).get('retina'):
                            extra['image'] = 'https:' + \
                                buddyicon['data']['retina']
                        if 'isPro' in person_model:
                            extra['is_pro'] = str(person_model['isPro'])

                    profile_model = find_model(data, 'person-profile-models')
                    if profile_model:
                        if profile_model.get('location'):
                            extra['location'] = profile_model['location']
                        if 'photoCount' in profile_model:
                            extra['photos_count'] = str(
                                profile_model['photoCount'])

                    contacts_model = find_model(
                        data, 'person-contacts-count-models')
                    if contacts_model:
                        if 'followerCount' in contacts_model:
                            extra['follower_count'] = str(
                                contacts_model['followerCount'])
                        if 'followingCount' in contacts_model:
                            extra['following_count'] = str(
                                contacts_model['followingCount'])
                except Exception:
                    pass

            return Result.taken(extra=extra, url=url)

        return Result.error(f"Unexpected status: {response.status_code}", url=url)

    except Exception as e:
        return Result.error(e, url=url)
