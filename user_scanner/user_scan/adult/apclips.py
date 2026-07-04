import re
import html
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate

def validate_apclips(user: str) -> Result:
    url = f"https://apclips.com/{user}"
    show_url = url

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        final_url = str(response.url)
        
        if final_url.endswith("/models") or "/models" in final_url:
            return Result.available()

        if response.status_code == 200:
            if "AP Model" in response.text or "profile-fit-text" in response.text:
                extra = {}

                name_match = re.search(
                    r'<h1 class="page-modelname[^"]*">\s*<span>([^<]+)</span>\s*</h1>',
                    response.text,
                    re.IGNORECASE
                )
                if name_match:
                    extra["name"] = html.unescape(name_match.group(1)).strip()

                def parse_stat(label):
                    match = re.search(
                        rf'<span class="stat-label">[^<]*{label}[^<]*</span>\s*<span class="stat-text">([^<]+)</span>',
                        response.text,
                        re.IGNORECASE | re.DOTALL
                    )
                    if match:
                        return match.group(1).strip()
                    return None

                videos = parse_stat("Videos")
                if videos:
                    extra["videos"] = videos

                views = parse_stat("Views")
                if views:
                    extra["views"] = views

                loves = parse_stat("Loves")
                if loves:
                    extra["loves"] = loves

                faved = parse_stat("Faved")
                if faved:
                    extra["faves"] = faved

                if not extra.get("videos"):
                    vid_match = re.search(r'<strong>(\d+)</strong>\s*Videos', response.text, re.IGNORECASE)
                    if vid_match:
                        extra["videos"] = vid_match.group(1)

                photo_match = re.search(r'<strong>(\d+)</strong>\s*Photosets', response.text, re.IGNORECASE)
                if photo_match:
                    extra["photosets"] = photo_match.group(1)

                desc_match = re.search(
                    r'<div class="text-medium[^"]*">\s*<p>([^<]+)</p>',
                    response.text,
                    re.IGNORECASE | re.DOTALL
                )
                if desc_match:
                    extra["bio"] = html.unescape(desc_match.group(1)).strip()

                return Result.taken(extra=extra)

        elif response.status_code == 404:
            return Result.available()

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, headers=headers, http2=False, show_url=show_url, follow_redirects=True)
