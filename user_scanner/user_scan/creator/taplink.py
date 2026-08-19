import json
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_taplink(user: str) -> Result:
    """Validate a username on Taplink (taplink.cc)."""
    url = f"https://taplink.cc/{user}"
    show_url = f"https://taplink.cc/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def process(response):
        response_text_lower = response.text.lower()

        # 1. Explicit verification of available / not-found state (HTTP 404 or generic fallback markers)
        if (
            response.status_code == 404
            or "landing page that drives your sales on instagram" in response_text_lower
            or "link in bio tool for instagram and tiktok - taplink" in response_text_lower
        ):
            return Result.available(url=show_url)

        # 2. Explicit verification of taken state + deep data extraction
        if response.status_code == 200 and "taplink" in response_text_lower:
            og_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text)
            account_match = re.search(r"window\.account\s*=\s*({.*?});", response.text)

            if og_title_match or account_match:
                extra = {}
                media = {}

                if og_title_match:
                    og_title = og_title_match.group(1).strip()
                    if og_title.endswith(" at Taplink") or " at Taplink" in og_title:
                        name = og_title.replace(" at Taplink", "").strip()
                        if name:
                            extra["name"] = name

                if account_match:
                    try:
                        account_data = json.loads(account_match.group(1))
                        if account_id := account_data.get("account_id"):
                            extra["account_id"] = str(account_id)
                        if profile_id := account_data.get("profile_id"):
                            extra["profile_id"] = str(profile_id)
                        if lang := account_data.get("language_code"):
                            extra["language"] = str(lang)
                        if tariff := account_data.get("tariff_current"):
                            extra["plan"] = str(tariff)
                    except Exception:
                        pass

                og_img_match = re.search(r'<meta property="og:image" content="(.*?)"', response.text)
                if og_img_match:
                    img_url = og_img_match.group(1).strip()
                    if img_url and not img_url.endswith("taplink-opengraph.jpg"):
                        if img_url.startswith("//"):
                            img_url = f"https:{img_url}"
                        media["avatar"] = img_url

                if extra or media:
                    return Result.taken(extra=extra, media=media, url=show_url)

            return Result.error("Could not verify profile details on Taplink", url=show_url)

        # 3. Graceful error for unexpected status codes (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
