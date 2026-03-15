from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_riot_id(user: str) -> Result:
    """Check if a Riot ID (Name#Tag) is registered across Riot Games titles."""
    show_url = "https://www.riotid-lookup.com"

    user = user.strip()
    if user.count("#") != 1:
        return Result.error("Riot ID format required: Name#Tag (e.g. TenZ#00005)")

    name, tag = user.split("#")
    if not name or not tag:
        return Result.error("Both name and tag are required (e.g. TenZ#00005)")

    if not (3 <= len(tag) <= 5):
        return Result.error("Tag must be 3-5 characters")

    encoded = user.replace("#", "%23")
    url = f"https://www.riotid-lookup.com/api/lookup?riotId={encoded}"

    def process(response):
        if response.status_code == 200:
            data = response.json()
            if data.get("isTaken"):
                return Result.taken()
            return Result.available()

        if response.status_code == 400:
            return Result.error("Invalid Riot ID format")

        return Result.error(f"HTTP {response.status_code}")

    return generic_validate(url, process, show_url=show_url)
