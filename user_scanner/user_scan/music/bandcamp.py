from user_scanner.core.orchestrator import generic_validate, Result


def validate_bandcamp(user):
    url = f"https://bandcamp.com/{user}"
    show_url = f"https://bandcamp.com/{user}"

    def process(response):
        if response.status_code == 200 and " collection | Bandcamp</title>" in response.text:
            extra = {}
            try:
                import re as local_re
                import html as local_html
                import json as local_json
                m = local_re.search(r'data-blob=\"([^\"]+)\"', response.text)
                if m:
                    blob_data = local_json.loads(local_html.unescape(m.group(1)))
                    fan = blob_data.get("fan_data", {})
                    if fan:
                        if fan.get("fan_id"):
                            extra["id"] = fan.get("fan_id")
                        if fan.get("name"):
                            extra["name"] = fan.get("name")
                        if fan.get("location"):
                            extra["location"] = fan.get("location")
                        if fan.get("bio"):
                            extra["bio"] = fan.get("bio")
                        if fan.get("website_url"):
                            extra["website"] = fan.get("website_url")
                        if fan.get("followers_count") is not None:
                            extra["followers"] = fan.get("followers_count")
                        if fan.get("following_bands_count") is not None:
                            extra["following_bands"] = fan.get("following_bands_count")
                        if fan.get("following_fans_count") is not None:
                            extra["following_fans"] = fan.get("following_fans_count")
                        if fan.get("fav_genre"):
                            extra["fav_genre"] = fan.get("fav_genre")
                        if fan.get("photo") and isinstance(fan["photo"], dict) and fan["photo"].get("image_id"):
                            img_id = fan["photo"]["image_id"]
                            extra["avatar"] = f"https://f4.bcbits.com/img/00{img_id}_10.jpg"
            except Exception:
                pass
            return Result.taken(extra=extra)

        if response.status_code == 404 or "<h2>Sorry, that something isn’t here.</h2>" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

