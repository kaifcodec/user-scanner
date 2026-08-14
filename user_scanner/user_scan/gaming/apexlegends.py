from user_scanner.core.impersonate import impersonate_request
from user_scanner.core.result import Result

API_URL = "https://api.tracker.gg/api/v2/apex/standard/profile"
PROFILE_URL = "https://apex.tracker.gg/apex/profile"

# Apex accounts are per-platform: a handle can resolve on PSN and miss on the
# other two, so a single namespace never settles availability.
PLATFORMS = {"origin": "EA", "psn": "PlayStation", "xbl": "Xbox"}

HEADERS = {
    "Accept-Language": "en-US,en;q=0.5",
    "Origin": "https://apex.tracker.gg",
    "Referer": "https://apex.tracker.gg/",
}


def validate_apexlegends(user: str) -> Result:
    show_url = f"{PROFILE_URL}/origin/{user}/overview"

    hits: dict[str, dict] = {}
    errors: list[str] = []

    for platform in PLATFORMS:
        try:
            response = impersonate_request(
                f"{API_URL}/{platform}/{user}", headers=HEADERS
            )
        except Exception as e:
            return Result.error(e, url=show_url)

        if response.status_code == 404:
            continue

        if response.status_code in (403, 429):
            errors.append(f"{platform}: blocked by anti-bot protection ({response.status_code})")
            continue

        if response.status_code != 200:
            errors.append(f"{platform}: unexpected status {response.status_code}")
            continue

        try:
            data = response.json().get("data") or {}
        except Exception:
            errors.append(f"{platform}: 200 response with unparseable body")
            continue

        if data.get("platformInfo", {}).get("platformSlug") != platform:
            errors.append(f"{platform}: 200 response with no recognizable profile")
            continue

        hits[platform] = data

    if hits:
        extra, media = _extract(hits)
        first = next(iter(hits))
        return Result.taken(extra=extra, media=media, url=f"{PROFILE_URL}/{first}/{user}/overview")

    # A blocked leg proves nothing about the handle; only an all-clear miss does.
    if errors:
        return Result.error("; ".join(errors), url=show_url)

    return Result.available(url=show_url)


def _extract(hits: dict[str, dict]) -> tuple[dict, dict]:
    extra: dict = {"platforms": ", ".join(PLATFORMS[p] for p in hits)}
    media: dict = {}

    for platform, data in hits.items():
        prefix = f"{platform}_" if len(hits) > 1 else ""

        p_info = data.get("platformInfo") or {}
        if handle := p_info.get("platformUserHandle"):
            extra[f"{prefix}username"] = handle
        if avatar := p_info.get("avatarUrl"):
            media.setdefault(f"{prefix}avatar", avatar)

        u_info = data.get("userInfo") or {}
        if country := u_info.get("countryCode"):
            extra[f"{prefix}country"] = country
        if u_info.get("isPremium"):
            extra[f"{prefix}premium"] = "Yes"
        if u_info.get("isInfluencer"):
            extra[f"{prefix}influencer"] = "Yes"

        if legend := (data.get("metadata") or {}).get("activeLegendName"):
            extra[f"{prefix}active_legend"] = legend

        segments = data.get("segments") or []
        stats = segments[0].get("stats", {}) if segments else {}
        if level := stats.get("level"):
            extra[f"{prefix}level"] = str(level.get("displayValue"))
        if kills := stats.get("kills"):
            extra[f"{prefix}kills"] = str(kills.get("displayValue"))

    return extra, media
