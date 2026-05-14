import httpx
from datetime import datetime
from user_scanner.core.result import Result

async def _check(email: str) -> Result:
    url = "https://www.etsy.com/api/v3/ajax/public/users/by-identity-optional"
    show_url = "https://www.etsy.com"

    params = {'identity': email}

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "identity",
        'x-detected-locale': "INR|en-IN|IN",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Brave";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': "?1",
        'Content-Type': "application/json",
        'Referer': "https://www.etsy.com/join/email",
        'Priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 403:
                return Result.error("403")

            if response.text.strip() == "null":
                return Result.available(url=show_url)

            data = response.json()

            if data.get("user_id"):
                # profile Basics
                user_id = data.get("user_id")
                real_name = data.get("real_name") or data.get("display_name")
                login_name = data.get("login_name")
                gender = data.get("gender")
                location = data.get("location")
                bio = data.get("bio", "").strip()

                # account roles, Flags
                is_seller = "Yes" if data.get("is_seller") is True else "No"
                has_page = "Yes" if data.get("has_page") is True else "No"

                # Privacy / Public Visibility Configs
                fav_items = "Public" if data.get("favorite_items_public") is True else "Private"
                fav_shops = "Public" if data.get("favorite_shops_public") is True else "Private"

                # stats
                followers = data.get("follower_count", 0)
                following = data.get("following_count", 0)
                favs = data.get("num_favorites", 0)

                # avatar logic (extracting the high-res 400x400 source if available)
                pfp = "No PFP"
                if data.get("has_avatar") or data.get("avatar_url"):
                    pfp = data.get("avatar_url")
                    avatar_dict = data.get("avatar")
                    if isinstance(avatar_dict, dict) and avatar_dict.get("url"):
                        pfp = str(avatar_dict.get("url"))

                # date formatting
                created = data.get("create_date")
                updated = data.get("update_date")

                date_created = datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S') if created else "Unknown"
                date_updated = datetime.fromtimestamp(updated).strftime('%Y-%m-%d %H:%M:%S') if updated else None

                # Build the full structured list
                info_parts = [
                    f"ID: {user_id}",
                    f"Name: {real_name}" if real_name else "Name: N/A",
                    f"Username: {login_name}" if login_name else "Username: N/A",
                    f"Gender: {gender}" if gender else None,
                    f"Location: {location}" if location else None,
                    f"Bio: {bio}" if bio else None,
                    f"Is Seller: {is_seller}",
                    f"Has Public Page: {has_page}",
                    f"Stats: {followers} followers | {following} following | {favs} favorites",
                    f"Privacy: Items are {fav_items} | Shops are {fav_shops}",
                    f"Joined: {date_created}",
                ]

                if date_updated:
                    info_parts.append(f"Last Profile Update: {date_updated}")

                info_parts.append(f"Avatar: {pfp}")

                extra_str = "\n".join(filter(None, info_parts))
                return Result.taken(url=show_url, extra=extra_str)

            return Result.error("Unexpected response body structure")

    except Exception as e:
        return Result.error(e)

async def validate_etsy(email: str) -> Result:
    return await _check(email)
