import hashlib
import httpx
from user_scanner.core.result import Result

def _extract_profile_data(entry: dict, extra: dict) -> None:
    if entry.get("preferredUsername"):
        extra["username"] = str(entry["preferredUsername"]).strip()
    if entry.get("displayName"):
        extra["display_name"] = str(entry["displayName"]).strip()
    if entry.get("profileUrl"):
        extra["profile_url"] = str(entry["profileUrl"]).strip()
    if entry.get("thumbnailUrl"):
        extra["thumbnail_url"] = str(entry["thumbnailUrl"]).strip()
    if entry.get("aboutMe"):
        extra["bio"] = str(entry["aboutMe"]).strip()
    if entry.get("currentLocation"):
        extra["location"] = str(entry["currentLocation"]).strip()
    if entry.get("jobTitle"):
        extra["job_title"] = str(entry["jobTitle"]).strip()
    if entry.get("company"):
        extra["company"] = str(entry["company"]).strip()

    name_info = entry.get("name")
    if isinstance(name_info, dict) and name_info.get("formatted"):
        extra["full_name"] = str(name_info["formatted"]).strip()

    photos = entry.get("photos")
    if isinstance(photos, list):
        photo_list = [
            str(p["value"]).strip()
            for p in photos
            if isinstance(p, dict) and p.get("value") is not None and str(p["value"]).strip()
        ]
        if photo_list:
            extra["photos"] = ", ".join(photo_list)

    accounts = entry.get("accounts")
    if isinstance(accounts, list):
        acc_list = []
        for acc in accounts:
            if not isinstance(acc, dict):
                continue
            acc_name = str(acc.get("name") or acc.get("shortname") or "Account")
            acc_url = acc.get("url") or acc.get("display") or acc.get("username")
            if acc_url is not None and str(acc_url).strip():
                status = " (verified)" if acc.get("verified") else ""
                acc_list.append(f"{acc_name}: {str(acc_url).strip()}{status}")
        if acc_list:
            extra["verified_accounts"] = ", ".join(acc_list)

    urls = entry.get("urls")
    if isinstance(urls, list):
        url_list = [
            str(u["value"]).strip()
            for u in urls
            if isinstance(u, dict) and u.get("value") is not None and str(u["value"]).strip()
        ]
        if url_list:
            extra["websites"] = ", ".join(url_list)

    emails = entry.get("emails")
    if isinstance(emails, list):
        email_list = [
            str(e["value"]).strip()
            for e in emails
            if isinstance(e, dict) and e.get("value") is not None and str(e["value"]).strip()
        ]
        if email_list:
            extra["public_emails"] = ", ".join(email_list)

    crypto = entry.get("crypto")
    if isinstance(crypto, list):
        crypto_list = [
            f"{str(c.get('currency', 'Wallet'))}: {str(c['value']).strip()}"
            for c in crypto
            if isinstance(c, dict) and c.get("value") is not None and str(c["value"]).strip()
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
