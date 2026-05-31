from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_github(user):
    url = f"https://github.com/{user}"
    show_url = f"https://github.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def process(response):
        if response.status_code == 404:
            return Result.available()
        elif response.status_code == 200:
            extra = {}
            try:
                import re as local_re
                # 1. Name
                name_match = local_re.search(r'itemprop="name">\s*([^<\n\r]+)\s*</span>', response.text)
                if name_match:
                    extra["name"] = name_match.group(1).strip()
                # 2. Bio
                bio_match = local_re.search(r'class="p-note user-profile-bio[^"]*"[^>]*><div>([^<]+)</div>', response.text)
                if bio_match:
                    extra["bio"] = bio_match.group(1).strip()
                # 3. Company
                company_match = local_re.search(r'itemprop="worksFor"[^>]*aria-label="Organization:\s*([^"]+)"', response.text)
                if company_match:
                    extra["company"] = company_match.group(1).strip()
                # 4. Location
                loc_match = local_re.search(r'itemprop="homeLocation"[^>]*aria-label="Home location:\s*([^"]+)"', response.text)
                if loc_match:
                    extra["location"] = loc_match.group(1).strip()
                # 5. Website
                web_match = local_re.search(r'itemprop="url"[^>]*>.*?href="([^"]+)"', response.text, local_re.DOTALL)
                if web_match:
                    extra["website"] = web_match.group(1).strip()
                # 6. Email
                email_match = local_re.search(r'itemprop="email"[^>]*>.*?href="mailto:([^"]+)"', response.text, local_re.DOTALL)
                if email_match:
                    extra["email"] = email_match.group(1).strip()
                # 7. Followers
                followers_match = local_re.search(r'class="text-bold color-fg-default">([0-9.]+[kM]?)</span>\s*followers', response.text)
                if followers_match:
                    extra["followers"] = followers_match.group(1)
                # 8. Following
                following_match = local_re.search(r'class="text-bold color-fg-default">([0-9.]+[kM]?)</span>\s*following', response.text)
                if following_match:
                    extra["following"] = following_match.group(1)
                # 9. Avatar
                avatar_match = local_re.search(r'itemprop="image"\s+href="([^"]+)"', response.text)
                if avatar_match:
                    extra["avatar"] = avatar_match.group(1).replace("&amp;", "&")
                # 10. Organizations
                orgs = local_re.findall(r'data-hovercard-type="organization"[^>]*href="/([^/"]+)"', response.text)
                if orgs:
                    unique_orgs = list(dict.fromkeys(orgs))
                    extra["organizations"] = ", ".join(unique_orgs)
                # 11. Social Media Links
                socials = local_re.findall(r'itemprop="social".*?href="([^"]+)"', response.text, local_re.DOTALL)
                if socials:
                    for s in socials:
                        domain_match = local_re.search(r'https?://(?:www\.)?([^/]+)', s)
                        if domain_match:
                            domain = domain_match.group(1).split(".")[0].capitalize()
                            extra[domain] = s
                        else:
                            extra["social_profile"] = s
            except Exception:
                pass
            return Result.taken(extra=extra)
        else:
            return Result.error(f"Unexpected status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, headers=headers)


