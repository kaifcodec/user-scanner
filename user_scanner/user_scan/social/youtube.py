import json
import re

import httpx

from user_scanner.core.orchestrator import Result, make_request


def validate_youtube(user) -> Result:
    url = f"https://www.youtube.com/@{user}?cbrd=1&ucbcb=1"
    show_url = f"https://youtube.com/@{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = make_request(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            if "This channel does not exist" in response.text or "404 Not Found" in response.text:
                return Result.available(url=show_url)

            extra = {}
            media = {}
            marker = "var ytInitialData = "
            start = response.text.find(marker)
            if start == -1:
                return Result.error("Could not confirm YouTube channel", url=show_url)

            try:
                data = json.JSONDecoder().raw_decode(response.text[start + len(marker) :])[0]
                meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
                channel_id = meta.get("externalId")
                if not re.fullmatch(r"UC[\w-]+", channel_id or ""):
                    return Result.error("Could not confirm YouTube channel", url=show_url)
                extra["youtube_channel_id"] = channel_id
                extra["channel_url"] = f"https://www.youtube.com/channel/{channel_id}"
                if title := meta.get("title"):
                    extra["fullname"] = title
                if desc := meta.get("description"):
                    extra["bio"] = desc
                if keywords := meta.get("keywords"):
                    extra["keywords"] = keywords
                if thumbs := meta.get("avatar", {}).get("thumbnails"):
                    media["image"] = thumbs[0].get("url")
            except json.JSONDecodeError:
                return Result.error("Could not confirm YouTube channel", url=show_url)

            subs = re.search(r'\"content\":\"([0-9.]+[A-Z]? subscribers)\"', response.text)
            if subs:
                extra["subscribers"] = subs.group(1)

            return Result.taken(extra=extra, media=media, url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
    except httpx.HTTPError as e:
        return Result.error(e, url=show_url)
