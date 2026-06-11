from user_scanner.core.orchestrator import generic_validate, Result
from user_scanner.core.helpers import get_random_user_agent
import re as local_re

def validate_hamaha(user):
    url = f"https://hamaha.net/{user}/tab:info"
    show_url = f"https://hamaha.net/{user}"

    headers = {
        "User-Agent": get_random_user_agent()
    }

    def process(response):
        if 'id="profile"' in response.text:
            extra = {}
            try:
                name_match = local_re.search(r'<h2>(.*?)</h2>', response.text)
                if name_match:
                    name_val = name_match.group(1).strip()
                    if name_val:
                        extra["name"] = name_val

                avatar_match = local_re.search(r'<div id="profileavatar"><img src="([^"]+)"/></div>', response.text)
                if avatar_match:
                    avatar_val = avatar_match.group(1).strip()
                    if "_noavatar_user.gif" not in avatar_val:
                        extra["avatar"] = avatar_val

                bio_match = local_re.search(r'<h3>Обо мне</h3>.*?<td>(.*?)</td>', response.text, local_re.DOTALL)
                if bio_match:
                    extra["bio"] = bio_match.group(1).strip()

                trading_match = local_re.search(r'<h3>Я торгую на</h3>.*?<td>(.*?)</td>', response.text, local_re.DOTALL)
                if trading_match:
                    extra["trading"] = trading_match.group(1).strip()

                details = local_re.findall(r'<td class="detailsparam">([^:]+):</td>\s*<td class="detailsvalue">(.*?)</td>', response.text, local_re.DOTALL)
                for param, value in details:
                    param_clean = param.strip().lower()
                    value_clean = value.strip()
                    if "пол" in param_clean:
                        extra["gender"] = value_clean
                    elif "присоединился" in param_clean:
                        extra["joined"] = value_clean
                    elif "последний" in param_clean:
                        extra["last_seen"] = value_clean

                ext_matches = local_re.findall(r'href="(https?://[^"]+)"[^>]*target="_blank"', response.text)
                if ext_matches:
                    ext_links = [link for link in ext_matches if "hamaha.net" not in link]
                    if ext_links:
                        extra["links"] = ", ".join(list(dict.fromkeys(ext_links)))

            except Exception:
                pass
            return Result.taken(extra=extra)

        if 'content="HAMAHA  Биткоин форум' in response.text or 'быстрая регистрация' in response.text.lower():
            return Result.available()

        return Result.error("Unexpected response body.")

    return generic_validate(url, process, headers=headers, show_url=show_url)

