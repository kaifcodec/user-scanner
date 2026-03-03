from curl_cffi import requests as cf_requests
from user_scanner.core.result import Result


def validate_valorant(user: str) -> Result:
    """Check if a Valorant Riot ID (Name#Tag) exists via tracker.gg.

    Uses curl_cffi to bypass Cloudflare's TLS fingerprint detection.
    Riot IDs require the Name#Tag format (e.g. TenZ#00005).
    """
    show_url = "https://playvalorant.com"

    user = user.strip()
    if user.count("#") != 1:
        return Result.error("Riot ID format required: Name#Tag (e.g. TenZ#00005)")

    name, tag = user.split("#")
    if not name or not tag:
        return Result.error("Both name and tag are required (e.g. TenZ#00005)")

    encoded = user.replace("#", "%23")
    url = f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{encoded}"

    try:
        response = cf_requests.get(url, impersonate="chrome", timeout=10)

        if response.status_code == 200:
            return Result.taken(url=show_url)

        if response.status_code == 451:
            return Result.taken(url=show_url)

        if response.status_code == 404:
            body = response.text
            if "has not played" in body:
                return Result.taken(url=show_url)
            return Result.available(url=show_url)

        return Result.error(f"HTTP {response.status_code}")

    except Exception as e:
        return Result.error(f"Unexpected exception: {e}")


if __name__ == "__main__":
    user = input("Riot ID (Name#Tag): ").strip()
    result = validate_valorant(user)
    print(result)
