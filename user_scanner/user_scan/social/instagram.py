import html
import json
import re
from typing import Any

from user_scanner.core.impersonate import get_impersonate_timeout, get_warm_session
from user_scanner.core.orchestrator import Result


def validate_instagram(user: str) -> Result:
    if not (1 <= len(user) <= 30):
        return Result.error("Length must be between 1 and 30 characters")

    if not re.match(r"^[a-zA-Z0-9._]+$", user):
        return Result.error(
            "Instagram usernames can only use letters, numbers, underscores, and periods"
        )

    show_url = f"https://www.instagram.com/{user}/"
    warmup_url = "https://www.instagram.com/accounts/emailsignup/"

    try:
        session = get_warm_session("chrome", warmup_url=warmup_url)
        timeout = get_impersonate_timeout()

        # Step 1: Probe public profile page
        response = session.get(show_url, timeout=timeout, allow_redirects=False)
        if response.status_code == 200:
            html_text = response.text
            og_title_m = re.search(r'property="og:title" content="(.*?)"', html_text)
            og_title = html.unescape(og_title_m.group(1)) if og_title_m else ""

            # Check if this is an authentic profile page for the requested username
            if f"(@{user.lower()})" in og_title.lower():
                extra: dict[str, Any] = {}
                media: dict[str, str] = {}

                # Full name from og:title
                if "(@" in og_title:
                    fullname = og_title.split("(@")[0].strip()
                    if fullname and fullname.lower() != user.lower():
                        extra["fullname"] = fullname

                # Social metrics from og:description
                og_desc_m = re.search(r'property="og:description" content="(.*?)"', html_text)
                if og_desc_m:
                    og_desc = html.unescape(og_desc_m.group(1))
                    stats_m = re.search(
                        r"([0-9.,]+[A-Za-z]?)\s*Followers,\s*([0-9.,]+[A-Za-z]?)\s*Following,\s*([0-9.,]+[A-Za-z]?)\s*Posts",
                        og_desc,
                        re.IGNORECASE,
                    )
                    if stats_m:
                        extra["follower_count"] = stats_m.group(1)
                        extra["following_count"] = stats_m.group(2)
                        extra["post_count"] = stats_m.group(3)

                # Bio from meta description
                meta_desc_m = re.search(r'<meta content="(.*?)" name="description"', html_text)
                if meta_desc_m:
                    meta_desc = html.unescape(meta_desc_m.group(1))
                    bio_m = re.search(r'on Instagram:\s*"(.*)"', meta_desc, re.DOTALL)
                    if bio_m and bio_m.group(1).strip():
                        extra["bio"] = bio_m.group(1).strip()

                # Avatar image from og:image
                og_img_m = re.search(r'property="og:image" content="(.*?)"', html_text)
                if og_img_m:
                    img_url = html.unescape(og_img_m.group(1)).strip()
                    if img_url and "static.cdninstagram.com/rsrc.php" not in img_url:
                        media["avatar"] = img_url

                # Attempt deep JSON metadata extraction from embedded relay cache
                try:
                    scripts = re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', html_text)
                    for sc in scripts:
                        if "xig_user_by_username" in sc:
                            data = json.loads(sc)

                            def _find_user(obj: Any) -> Any:
                                if isinstance(obj, dict):
                                    for k, v in obj.items():
                                        if k == "xig_user_by_username":
                                            return v
                                        found = _find_user(v)
                                        if found is not None:
                                            return found
                                elif isinstance(obj, list):
                                    for item in obj:
                                        found = _find_user(item)
                                        if found is not None:
                                            return found
                                return None

                            user_info = _find_user(data)
                            if isinstance(user_info, dict):
                                if user_info.get("pk"):
                                    extra["id"] = user_info["pk"]
                                if user_info.get("full_name"):
                                    extra["fullname"] = user_info["full_name"]
                                if user_info.get("biography"):
                                    extra["bio"] = user_info["biography"]
                                if user_info.get("is_verified") is not None:
                                    extra["verified"] = str(user_info["is_verified"])
                                if user_info.get("is_private") is not None:
                                    extra["private"] = str(user_info["is_private"])
                                if user_info.get("profile_pic_url"):
                                    media["avatar"] = user_info["profile_pic_url"]
                                bio_links = user_info.get("bio_links")
                                if isinstance(bio_links, list) and bio_links:
                                    first_link = bio_links[0]
                                    if isinstance(first_link, dict) and first_link.get("url"):
                                        extra["external_url"] = first_link["url"]
                            break
                except Exception:
                    pass

                return Result.taken(extra=extra, media=media, url=show_url)

        # Step 2: Fallback to registration endpoint for accounts that are private,
        # age-gated, shadowbanned, redirecting, or non-existent
        csrf = session.cookies.get("csrftoken", "")
        if not csrf:
            session.get(warmup_url, timeout=timeout)
            csrf = session.cookies.get("csrftoken", "")

        signup_url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
        signup_headers = {
            "Accept": "*/*",
            "x-ig-app-id": "936619743392459",
            "x-csrftoken": csrf,
            "x-requested-with": "XMLHttpRequest",
            "referer": warmup_url,
            "content-type": "application/x-www-form-urlencoded",
        }
        signup_data = {
            "username": user,
            "email": "",
            "first_name": "",
            "opt_into_one_tap": "false",
        }

        signup_resp = session.post(
            signup_url, headers=signup_headers, data=signup_data, timeout=timeout
        )

        if signup_resp.status_code == 200:
            try:
                signup_data_res = signup_resp.json()
            except Exception:
                signup_data_res = {}

            errors = signup_data_res.get("errors", {})
            username_errors = errors.get("username")

            if username_errors:
                for err in username_errors:
                    code = err.get("code")
                    if code in (
                        "username_invalid",
                        "username_is_taken",
                        "username_invalid_substring",
                    ):
                        return Result.taken(url=show_url)
                    elif code in ("username_has_special_char", "username_too_long"):
                        return Result.error(
                            err.get("message", "Invalid username"), url=show_url
                        )

            if signup_data_res.get("status") == "ok" and not username_errors:
                return Result.available(url=show_url)

        elif signup_resp.status_code in (401, 403, 429):
            return Result.error(
                f"Rate limit / Cloudflare protection block (HTTP {signup_resp.status_code}). Run with residential proxy or active session cookies.",
                url=show_url,
            )

        return Result.error(
            f"Unexpected status: {signup_resp.status_code}", url=show_url
        )

    except Exception as e:
        return Result.error(e, url=show_url)
