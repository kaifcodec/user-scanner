import html
import json
import re
from urllib.parse import quote

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import make_request
from user_scanner.core.result import Result


def validate_stackb(user: str) -> Result:
    profile_url = f"https://stackb.net/@{user}"
    url = f"https://stackb.net/@{quote(user, safe='')}"
    login_url = "https://stackb.net/login"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }

    try:
        login_response = make_request(login_url, headers=headers, follow_redirects=True)
        if login_response.status_code != 200:
            return Result.error(f"Unexpected login status: {login_response.status_code}", url=url)

        login_text = login_response.text
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', login_text)
        snapshot_match = re.search(
            r'<div wire:snapshot="([^"]+)"[^>]*wire:id="([^"]+)"[^>]*x-data="loginFormCaptcha',
            login_text,
        )
        if not csrf_match or not snapshot_match:
            return Result.error("Could not find login form tokens", url=url)

        csrf_token = html.unescape(csrf_match.group(1))
        snapshot = html.unescape(snapshot_match.group(1))
        payload = {
            "_token": csrf_token,
            "components": [
                {
                    "snapshot": snapshot,
                    "updates": {
                        "identifier": user,
                        "password": "StackB-not-the-password-12345",
                    },
                    "calls": [{"path": "", "method": "submitLogin", "params": []}],
                }
            ],
        }
        login_check = make_request(
            "https://stackb.net/livewire/update",
            method="POST",
            headers={
                **headers,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://stackb.net",
                "Referer": login_url,
                "X-CSRF-TOKEN": csrf_token,
                "X-Livewire": "true",
            },
            json=payload,
        )

        if login_check.status_code != 200:
            return Result.error(f"Unexpected login check status: {login_check.status_code}", url=url)

        try:
            login_data = login_check.json()
            login_messages = " ".join(
                str(dispatch.get("params", {}).get("message", ""))
                for component in login_data.get("components", [])
                for dispatch in component.get("effects", {}).get("dispatches", [])
            )
        except (ValueError, AttributeError):
            return Result.error("Unexpected login check response", url=url)

        if "Максимальная длина никнейма" in login_messages:
            return Result.available(
                "Username format rejected by StackB",
                url=url,
            )
        if "Таких пользователей не нашлось" in login_messages:
            return Result.available(url=url)
        if "Пароль введен неверно" not in login_messages:
            return Result.error("Unexpected login check response", url=url)

        extra = {}
        try:
            profile_response = make_request(
                url,
                headers=headers,
                show_url=url,
                follow_redirects=True,
            )
            response_text = profile_response.text
            profile = {}
            for json_match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', response_text, re.DOTALL):
                try:
                    data = json.loads(html.unescape(json_match.group(1)))
                except json.JSONDecodeError:
                    continue

                if data.get("@type") == "ProfilePage":
                    entity = data.get("mainEntity")
                    if isinstance(entity, dict):
                        profile = entity
                    break

            if profile:
                description_match = re.search(r'<meta [^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']*)', response_text, re.IGNORECASE)
                stats_text = html.unescape(description_match.group(1)).strip() if description_match else None

                if name := profile.get("name"): extra["display_name"] = name
                if description := profile.get("description"): extra["bio"] = description
                if image := profile.get("image"): extra["avatar"] = image

                if stats_text:
                    if rank_match := re.search(r"Ранг:\s*([^\.]+)", stats_text):
                        extra["rank"] = rank_match.group(1).strip()
                    if followers_match := re.search(r"Подписчики:\s*(\d+)", stats_text):
                        extra["followers"] = int(followers_match.group(1))

                extra["profile_url"] = profile_url
        except Exception:
            pass

        return Result.taken(extra=extra, url=url)
    except Exception as exc:
        return Result.error(exc, url=url)
