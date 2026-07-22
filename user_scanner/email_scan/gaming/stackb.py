import html
import re

import httpx

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    show_url = "https://stackb.net"
    login_url = f"{show_url}/login"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            headers=headers,
            follow_redirects=True,
        ) as client:
            login_response = await client.get(login_url)
            if login_response.status_code != 200:
                return Result.error(
                    f"Unexpected login status: {login_response.status_code}",
                    url=show_url,
                )

            csrf_match = re.search(
                r'<meta name="csrf-token" content="([^"]+)"',
                login_response.text,
            )
            snapshot_match = re.search(
                r'<div wire:snapshot="([^"]+)"[^>]*wire:id="[^"]+"'
                r'[^>]*x-data="loginFormCaptcha',
                login_response.text,
            )
            if not csrf_match or not snapshot_match:
                return Result.error(
                    "Could not find login form tokens",
                    url=show_url,
                )

            csrf_token = html.unescape(csrf_match.group(1))
            payload = {
                "_token": csrf_token,
                "components": [
                    {
                        "snapshot": html.unescape(snapshot_match.group(1)),
                        "updates": {
                            "identifier": email,
                            "password": "StackB-not-the-password-12345",
                        },
                        "calls": [
                            {"path": "", "method": "submitLogin", "params": []}
                        ],
                    }
                ],
            }
            login_check = await client.post(
                f"{show_url}/livewire/update",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": show_url,
                    "Referer": login_url,
                    "X-CSRF-TOKEN": csrf_token,
                    "X-Livewire": "true",
                },
                json=payload,
            )

            if login_check.status_code != 200:
                return Result.error(
                    f"Unexpected login check status: {login_check.status_code}",
                    url=show_url,
                )

            components = login_check.json().get("components", [])
            login_messages = " ".join(
                str(dispatch.get("params", {}).get("message", ""))
                for component in components
                for dispatch in component.get("effects", {}).get(
                    "dispatches", []
                )
            )

            if "Таких пользователей не нашлось" in login_messages:
                return Result.available(url=show_url)
            if "Пароль введен неверно" in login_messages:
                return Result.taken(url=show_url)
            return Result.error("Unexpected login check response", url=show_url)
    except Exception as exc:
        return Result.error(exc, url=show_url)


async def validate_stackb(email: str) -> Result:
    return await _check(email)
