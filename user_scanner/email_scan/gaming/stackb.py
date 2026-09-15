import html
import re

import httpx

from user_scanner.core.helpers import get_global_timeout
from user_scanner.core.result import Result


async def validate_stackb(email: str) -> Result:
    show_url = "https://stackb.net"
    login_url = f"{show_url}/login"

    try:
        async with httpx.AsyncClient(timeout=get_global_timeout() or 15.0) as client:
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
                r'<div(?=[^>]*wire:name="login-form")'
                r'(?=[^>]*wire:snapshot="([^"]+)")[^>]*>',
                login_response.text,
            )
            if not csrf_match or not snapshot_match:
                return Result.error(
                    "Could not find login form tokens",
                    url=show_url,
                )

            csrf_token = html.unescape(csrf_match.group(1))
            payload = {
                "components": [
                    {
                        "snapshot": html.unescape(snapshot_match.group(1)),
                        "updates": {
                            "identifier": email,
                            "password": "StackB-not-the-password-12345",
                        },
                        "calls": [{"path": "", "method": "submitLogin", "params": []}],
                    }
                ],
            }
            login_check = await client.post(
                f"{show_url}/livewire/update",
                headers={
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

            login_messages = str(login_check.json().get("components", []))

            if "Таких пользователей не нашлось" in login_messages:
                return Result.available(url=show_url)
            if "Пароль введен неверно" in login_messages:
                return Result.taken(url=show_url)
            return Result.error("Unexpected login check response", url=show_url)
    except (httpx.HTTPError, ValueError, AttributeError) as exc:
        return Result.error(exc, url=show_url)
