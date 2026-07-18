import re
import json
import urllib.parse
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_flickr(user: str) -> Result:
    url = f"https://www.flickr.com/photos/{user}"
    show_url = f"https://www.flickr.com/photos/{user}"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            extra = {}
            match = re.search(r"modelExport:\s*(.*?),\s*auth", r.text)
            if match:
                try:
                    raw_encoded = match.group(1)
                    raw_decoded = urllib.parse.unquote(raw_encoded)
                    data = json.loads(raw_decoded)
                    main = data.get("main", {})

                    photostream = main.get("photostream-models", [{}])[0].get("data", {})
                    owner = photostream.get("owner", {}).get("data", {})
                    profile = main.get("person-profile-models", [{}])[0].get("data", {})
                    contacts = main.get("person-contacts-count-models", [{}])[0].get("data", {})

                    if owner.get("username"):
                        extra["display_name"] = owner.get("username")
                    if owner.get("realname"):
                        extra["fullname"] = owner.get("realname")
                    if profile.get("location"):
                        extra["location"] = profile.get("location")

                    avatar_retina = owner.get("buddyicon", {}).get("data", {}).get("retina") or owner.get("buddyicon", {}).get("retina")
                    if avatar_retina:
                        if avatar_retina.startswith("//"):
                            avatar_retina = "https:" + avatar_retina
                        extra["avatar_url"] = avatar_retina

                    if profile.get("photoCount") is not None:
                        extra["photos"] = int(profile.get("photoCount"))
                    if contacts.get("followerCount") is not None:
                        extra["followers"] = int(contacts.get("followerCount"))
                    if contacts.get("followingCount") is not None:
                        extra["following"] = int(contacts.get("followingCount"))

                except Exception:
                    pass

            return Result.taken(extra=extra)

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
