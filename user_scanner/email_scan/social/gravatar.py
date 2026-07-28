import hashlib
import httpx
from user_scanner.core.result import Result

def _extract_profile_data(entry: dict, extra: dict) -> None:
    if entry.get("preferredUsername"):
        extra["username"] = entry["preferredUsername"]
    if entry.get("displayName"):
        extra["display_name"] = entry["displayName"]
    if entry.get("profileUrl"):
        extra["profile_url"] = entry["profileUrl"]
    if entry.get("thumbnailUrl"):
        extra["thumbnail_url"] = entry["thumbnailUrl"]
    if entry.get("aboutMe"):
        extra["bio"] = entry["aboutMe"].strip()
    if entry.get("currentLocation"):
        extra["location"] = entry["currentLocation"].strip()
    if entry.get("jobTitle"):
        extra["job_title"] = entry["jobTitle"].strip()
    if entry.get("company"):
        extra["company"] = entry["company"].strip()

    name_info = entry.get("name")
    if isinstance(name_info, dict) and name_info.get("formatted"):
        extra["full_name"] = name_info["formatted"].strip()

    photos = entry.get("photos", [])
    if photos and isinstance(photos, list):
        photo_list = [p.get("value").strip() for p in photos if isinstance(p, dict) and p.get("value")]
        if photo_list:
            extra["photos"] = ", ".join(photo_list)

    accounts = entry.get("accounts", [])
    if accounts and isinstance(accounts, list):
        acc_list = []
        for acc in accounts:
            if not isinstance(acc, dict):
                continue
            acc_name = acc.get("name") or acc.get("shortname") or "Account"
            acc_url = acc.get("url") or acc.get("display") or acc.get("username")
            if acc_url:
                status = " (verified)" if acc.get("verified") else ""
                acc_list.append(f"{acc_name}: {acc_url}{status}")
        if acc_list:
            extra["verified_accounts"] = ", ".join(acc_list)

    urls = entry.get("urls", [])
    if urls and isinstance(urls, list):
        url_list = [u.get("value").strip() for u in urls if isinstance(u, dict) and u.get("value")]
        if url_list:
            extra["websites"] = ", ".join(url_list)

    emails = entry.get("emails", [])
    if emails and isinstance(emails, list):
        email_list = [e.get("value").strip() for e in emails if isinstance(e, dict) and e.get("value")]
        if email_list:
            extra["public_emails"] = ", ".join(email_list)

    crypto = entry.get("crypto", [])
    if crypto and isinstance(crypto, list):
        crypto_list = [
            f"{c.get('currency', 'Wallet')}: {c.get('value').strip()}"
            for c in crypto
            if isinstance(c, dict) and c.get("value")
        ]
        if crypto_list:
            extra["crypto_addresses"] = ", ".join(crypto_list)

async def _check(email: str) -> Result:
    show_url = "https://gravatar.com"
    email_clean = email.lower().strip()
    email_hash = hashlib.sha256(email_clean.encode("utf-8")).hexdigest()
    url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                extra = {"avatar_url": f"https://www.gravatar.com/avatar/{email_hash}"}
                profile_url = f"https://en.gravatar.com/{email_hash}.json"
                try:
                    profile_resp = await client.get(profile_url, headers=headers, timeout=15.0)
                    if profile_resp.status_code == 200:
                        data = profile_resp.json()
                        entries = data.get("entry", [])
                        if entries and isinstance(entries, list):
                            _extract_profile_data(entries[0], extra)
                except Exception:
                    pass
                final_url = extra.get("profile_url", show_url)
                return Result.taken(url=final_url, extra=extra)
            elif response.status_code == 404:
                # Also fall back to check MD5 since some older profiles might only map via MD5
                email_md5 = hashlib.md5(email_clean.encode("utf-8")).hexdigest()
                url_md5 = f"https://www.gravatar.com/avatar/{email_md5}?d=404"
                
                response_md5 = await client.get(url_md5, headers=headers)
                if response_md5.status_code == 200:
                    extra = {"avatar_url": f"https://www.gravatar.com/avatar/{email_md5}"}
                    profile_url_md5 = f"https://en.gravatar.com/{email_md5}.json"
                    try:
                        profile_resp = await client.get(profile_url_md5, headers=headers, timeout=15.0)
                        if profile_resp.status_code == 200:
                            data = profile_resp.json()
                            entries = data.get("entry", [])
                            if entries and isinstance(entries, list):
                                _extract_profile_data(entries[0], extra)
                    except Exception:
                        pass
                    final_url = extra.get("profile_url", show_url)
                    return Result.taken(url=final_url, extra=extra)
                elif response_md5.status_code == 404:
                    return Result.available(url=show_url)
                else:
                    return Result.error(f"HTTP MD5 {response_md5.status_code}", url=show_url)
            return Result.error(f"HTTP {response.status_code}", url=show_url)
    except httpx.TimeoutException:
        return Result.error("Connection timed out", url=show_url)
    except Exception as e:
        return Result.error(e, url=show_url)

async def validate_gravatar(email: str) -> Result:
    return await _check(email)
