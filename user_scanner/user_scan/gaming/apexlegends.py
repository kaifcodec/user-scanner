from user_scanner.core.orchestrator import generic_validate, Result

def validate_apexlegends(user):
    url = f"https://api.tracker.gg/api/v2/apex/standard/profile/origin/{user}"
    show_url = f"https://apex.tracker.gg/apex/profile/origin/{user}/overview"

    headers = {
        "Accept-Language": "en-US,en;q=0.5",
        "Origin": "https://apex.tracker.gg",
        "Referer": "https://apex.tracker.gg/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    }

    def process(response):
        if response.status_code == 200:
            try:
                payload = response.json()
                data = payload.get("data", {})
                extra = {}
                
                p_info = data.get("platformInfo", {})
                if handle := p_info.get("platformUserHandle"): extra["username"] = handle
                if avatar := p_info.get("avatarUrl"): extra["avatar"] = avatar
                
                u_info = data.get("userInfo", {})
                if country := u_info.get("countryCode"): extra["country"] = country
                if u_info.get("isPremium"): extra["premium"] = "Yes"
                if u_info.get("isInfluencer"): extra["influencer"] = "Yes"
                
                meta = data.get("metadata", {})
                if legend := meta.get("activeLegendName"): extra["active_legend"] = legend
                
                segments = data.get("segments", [])
                if segments:
                    stats = segments[0].get("stats", {})
                    if lvl := stats.get("level"): extra["level"] = str(lvl.get("displayValue"))
                    if kills := stats.get("kills"): extra["kills"] = str(kills.get("displayValue"))
                
                return Result.taken(extra=extra)
            except Exception:
                pass
            return Result.error("200 response status with no recognizable data, report it via GitHub issues")

        if response.status_code == 404:
            return Result.available()

        if response.status_code in [403, 429]:
            return Result.error("Request blocked by anti-bot protection.")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return generic_validate(url, process, headers=headers, show_url=show_url)
