from datetime import datetime, timezone
import httpx
from user_scanner.core.result import Result


async def _check(email: str) -> Result:
    url = "https://www.etsy.com/api/v3/ajax/public/users/by-identity-optional"
    show_url = "https://www.etsy.com"

    params = {
        "identity": email,
        "features": "api.oauth2.consent_page:on,design_systems.signin_flow_experiment:on",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 11; RMX2193 Build/RP1A.200720.011; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/155.0.8059.46 "
            "Mobile Safari/537.36 Mobile/1 EtsyInc/8.1.0 Android/1"
        ),
        "Accept": "application/json, text/plain, */*",
        "x-etsy-protection": "1",
        "x-requested-with": "com.etsy.android",
        "content-type": "application/json",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://www.etsy.com/oauth2/signin",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Android WebView";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua-platform-version": '"11.0.0"',
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return Result.error("Caught by WAF (403)", url=show_url)
            if response.status_code == 429:
                return Result.error("Rate limited by Etsy (429)", url=show_url)
            if response.status_code != 200:
                return Result.error(
                    f"Unexpected response status: {response.status_code}", url=show_url
                )

            if response.text.strip() == "null":
                return Result.available(url=show_url)

            try:
                data = response.json()
            except Exception:
                return Result.error("Invalid JSON response payload", url=show_url)

            if not isinstance(data, dict):
                return Result.error("Unexpected response body format", url=show_url)

            if data.get("user_id"):
                user_id = data.get("user_id")
                real_name = data.get("real_name") or data.get("display_name")
                login_name = data.get("login_name")
                gender = data.get("gender")
                location = data.get("location")
                bio = (data.get("bio") or "").strip()

                is_seller = "Yes" if data.get("is_seller") is True else "No"
                has_page = "Yes" if data.get("has_page") is True else "No"

                fav_items = "Public" if data.get("favorite_items_public") is True else "Private"
                fav_shops = "Public" if data.get("favorite_shops_public") is True else "Private"

                followers = data.get("follower_count", 0)
                following = data.get("following_count", 0)
                favs = data.get("num_favorites", 0)

                created = data.get("create_date")
                updated = data.get("update_date")

                date_created = (
                    datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    if created
                    else None
                )
                date_updated = (
                    datetime.fromtimestamp(updated, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    if updated
                    else None
                )

                extras = {
                    "id": user_id,
                    "name": real_name or "N/A",
                    "username": login_name or "N/A",
                    "gender": gender,
                    "location": location,
                    "bio": bio,
                    "is seller": is_seller,
                    "has public page": has_page,
                    "stats": f"{followers} followers | {following} following | {favs} favorites",
                    "privacy": f"Items are {fav_items} | Shops are {fav_shops}",
                    "joined": date_created,
                    "last profile update": date_updated,
                }
                extras = {k: v for k, v in extras.items() if v is not None and v != ""}

                media = {}
                if data.get("has_avatar"):
                    avatar_dict = data.get("avatar")
                    if isinstance(avatar_dict, dict) and avatar_dict.get("url"):
                        media["avatar"] = str(avatar_dict.get("url"))
                    elif data.get("avatar_url"):
                        media["avatar"] = str(data.get("avatar_url"))

                return Result.taken(url=show_url, extra=extras, media=media)

            return Result.error("Unexpected response body structure", url=show_url)

    except Exception as e:
        return Result.error(e, url=show_url)


async def validate_etsy(email: str) -> Result:
    return await _check(email)
