import urllib.parse
from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.orchestrator import Result

def validate_artstation(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.artstation.com/users/{encoded_user}.json"
    show_url = f"https://{user.lower()}.artstation.com/"

    def process(response) -> Result:
        if response.status_code == 404:
            return Result.available(url=show_url)

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and (data.get("username") or data.get("full_name") or data.get("id")):
                    extra: dict[str, str] = {}
                    media: dict[str, str] = {}

                    if data.get("full_name"):
                        extra["name"] = str(data["full_name"])
                    if data.get("headline"):
                        extra["headline"] = str(data["headline"])
                    if data.get("username"):
                        extra["username"] = str(data["username"])
                    portfolio = data.get("portfolio") or {}
                    if portfolio.get("summary"):
                        extra["bio"] = str(portfolio["summary"])
                    if data.get("city"):
                        extra["city"] = str(data["city"])
                    if data.get("country"):
                        extra["country"] = str(data["country"])
                    if data.get("followers_count") is not None:
                        extra["followers"] = str(data["followers_count"])
                    if data.get("followees_count") is not None:
                        extra["following"] = str(data["followees_count"])
                    if data.get("projects_count") is not None:
                        extra["projects"] = str(data["projects_count"])
                    if data.get("liked_projects_count") is not None:
                        extra["likes"] = str(data["liked_projects_count"])
                    if data.get("is_plus_member"):
                        extra["plus_member"] = "true"
                    if data.get("is_staff"):
                        extra["staff"] = "true"
                    availability = []
                    if data.get("available_full_time"):
                        availability.append("full time")
                    if data.get("available_contract"):
                        availability.append("contract")
                    if data.get("available_freelance"):
                        availability.append("freelance")
                    if availability:
                        extra["availability"] = ", ".join(availability)
                    socials = [
                        str(data[k]) for k in (
                            "twitter_url", "facebook_url", "tumblr_url",
                            "deviantart_url", "linkedin_url",
                        ) if data.get(k)
                    ]
                    website = str(data.get("artstation_website") or "").strip()
                    default_hosts = {
                        str(data.get("artstation_subdomain_url") or "").replace("https://", "").replace("http://", ""),
                        str(data.get("profile_artstation_website_url") or "").replace("https://", "").replace("http://", ""),
                    }
                    if website and website not in default_hosts:
                        socials.append(website)
                    if socials:
                        extra["social"] = " ".join(socials)
                    if data.get("large_avatar_url"):
                        media["avatar"] = str(data["large_avatar_url"])
                    if data.get("default_cover_url"):
                        media["banner"] = str(data["default_cover_url"])

                    return Result.taken(url=show_url, extra=extra, media=media)
            except Exception:
                pass
            return Result.error("ArtStation 200 response missing valid user payload")

        return Result.error(f"Unexpected status code: {response.status_code}")

    return impersonate_validate(
        url,
        process,
        warmup_url="https://www.artstation.com/",
        impersonate="chrome120",
        show_url=show_url,
    )
