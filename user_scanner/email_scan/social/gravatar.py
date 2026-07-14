import hashlib
import httpx
from user_scanner.core.result import Result
async def _check(email: str) -> Result:
    show_url = "https://gravatar.com"
    email_clean = email.lower().strip()
    email_hash = hashlib.sha256(email_clean.encode("utf-8")).hexdigest()
    url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                extra = {"avatar_url": f"https://www.gravatar.com/avatar/{email_hash}"}
                # Optionally attempt to load public profile data for enriched metadata
                profile_url = f"https://en.gravatar.com/{email_hash}.json"
                try:
                    profile_resp = await client.get(profile_url, headers=headers, timeout=3.0)
                    if profile_resp.status_code == 200:
                        data = profile_resp.json()
                        entry = data.get("entry", [{}])[0]
                        if entry.get("preferredUsername"):
                            extra["username"] = entry["preferredUsername"]
                        if entry.get("displayName"):
                            extra["display_name"] = entry["displayName"]
                        if entry.get("profileUrl"):
                            extra["profile_url"] = entry["profileUrl"]
                except Exception:
                    pass
                return Result.taken(url=show_url, extra=extra)
            elif response.status_code == 404:
                # Also fall back to check MD5 since some older profiles might only map via MD5
                email_md5 = hashlib.md5(email_clean.encode("utf-8")).hexdigest()
                url_md5 = f"https://www.gravatar.com/avatar/{email_md5}?d=404"
                
                response_md5 = await client.get(url_md5, headers=headers)
                if response_md5.status_code == 200:
                    extra = {"avatar_url": f"https://www.gravatar.com/avatar/{email_md5}"}
                    profile_url_md5 = f"https://en.gravatar.com/{email_md5}.json"
                    try:
                        profile_resp = await client.get(profile_url_md5, headers=headers, timeout=3.0)
                        if profile_resp.status_code == 200:
                            data = profile_resp.json()
                            entry = data.get("entry", [{}])[0]
                            if entry.get("preferredUsername"):
                                extra["username"] = entry["preferredUsername"]
                            if entry.get("displayName"):
                                extra["display_name"] = entry["displayName"]
                            if entry.get("profileUrl"):
                                extra["profile_url"] = entry["profileUrl"]
                    except Exception:
                        pass
                    return Result.taken(url=show_url, extra=extra)
                elif response_md5.status_code == 404:
                    return Result.available(url=show_url)
                else:
                    return Result.error(f"HTTP MD5 {response_md5.status_code}")
            return Result.error(f"HTTP {response.status_code}")
    except httpx.TimeoutException:
        return Result.error("Connection timed out")
    except Exception as e:
        return Result.error(e)
async def validate_gravatar(email: str) -> Result:
    return await _check(email)
