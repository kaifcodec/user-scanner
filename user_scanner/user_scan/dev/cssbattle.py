import json
import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_cssbattle(user: str) -> Result:
    """Validate a username on CSSBattle (cssbattle.dev)."""
    url = f"https://cssbattle.dev/player/{user}"
    show_url = f"https://cssbattle.dev/player/{user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def process(response):
        if response.status_code == 200 and "cssbattle" in response.text.lower():
            next_data_match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">([\s\S]+?)</script>',
                response.text,
            )
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    page_props = data.get("props", {}).get("pageProps", {})
                    player = page_props.get("player")

                    if player is None:
                        return Result.available(url=show_url)

                    if isinstance(player, dict):
                        extra = {}
                        media = {}
                        if name := player.get("displayName"):
                            if str(name).strip() and str(name).lower() != "user":
                                extra["name"] = str(name).strip()
                        if username := player.get("username"):
                            extra["username"] = str(username).strip()
                        if avatar := player.get("avatar"):
                            if str(avatar).strip():
                                media["avatar"] = str(avatar).strip()

                        return Result.taken(extra=extra, media=media, url=show_url)
                except Exception:
                    pass
            return Result.available(url=show_url)
        elif response.status_code == 404:
            return Result.available(url=show_url)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(url, process, headers=headers, show_url=show_url, follow_redirects=True)
