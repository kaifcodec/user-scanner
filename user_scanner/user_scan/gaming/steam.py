from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result
import re as local_re
import html

def validate_steam(user):
    url = f"https://steamcommunity.com/id/{user}/"
    show_url = f"https://steamcommunity.com/id/{user}/"

    def process(response):
        if response.status_code == 200:
            if "Error</title>" in response.text:
                return Result.available()
            else:
                extra = {}
                steamid_match = local_re.search(r'"steamid"\s*:\s*"((?:[^"\\]|\\.)*)"', response.text)
                if steamid_match: extra["steam_id"] = steamid_match.group(1)

                personaname_match = local_re.search(r'"personaname"\s*:\s*"((?:[^"\\]|\\.)*)"', response.text)
                if personaname_match: 
                    extra["persona_name"] = html.unescape(personaname_match.group(1).replace(r'\/', '/').replace(r'\"', '"'))

                realname_match = local_re.search(r'class="header_real_name[^"]*">\s*<bdi>([^<]+)</bdi>', response.text)
                if realname_match: extra["real_name"] = html.unescape(realname_match.group(1).strip())

                loc_match = local_re.search(r'class="header_location"[^>]*>\s*(?:<img[^>]*>\s*)?([^<\r\n]+)', response.text)
                if loc_match: extra["location"] = html.unescape(loc_match.group(1).strip())

                avatar_match = local_re.search(r'class="playerAvatar profile_header_size.*?<picture>.*?<img srcset="([^"]+)"', response.text, local_re.DOTALL)
                if avatar_match:
                    extra["avatar"] = avatar_match.group(1).strip()
                else:
                    full_avatar_match = local_re.search(r'https?://avatars\.(?:fastly\.)?steamstatic\.com/[a-f0-9]+_full\.jpg', response.text)
                    if full_avatar_match:
                        extra["avatar"] = full_avatar_match.group(0)

                summary_match = local_re.search(r'"summary"\s*:\s*"((?:[^"\\]|\\.)*)"', response.text)
                if summary_match:
                    raw_summary = summary_match.group(1).replace(r'\/', '/').replace(r'\n', '\n').replace(r'\r', '\r').replace(r'\"', '"')
                    clean_summary = local_re.sub(r'<[^>]*>', '', raw_summary)
                    clean_summary = html.unescape(clean_summary).strip()
                    if clean_summary:
                        extra["summary"] = clean_summary

                return Result.taken(extra=extra)

        return Result.error("Invalid status code")

    return generic_validate(url, process, show_url=show_url)
