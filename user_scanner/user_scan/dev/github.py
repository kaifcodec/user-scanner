from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request
import re as local_re


def validate_github(user):
    api_url = f"https://api.github.com/users/{user}"
    show_url = f"https://github.com/{user}"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        api_response = make_request(api_url, headers=headers, follow_redirects=True)
        if api_response.status_code == 200:
            data = api_response.json()
            extra = {}
            if name := data.get("name"): extra["name"] = name
            if bio := data.get("bio"): extra["bio"] = bio
            if company := data.get("company"): extra["company"] = company
            if location := data.get("location"): extra["location"] = location
            if blog := data.get("blog"): extra["website"] = blog
            if email := data.get("email"):
                extra["email"] = email
            else:
                try:
                    html_headers = {
                        "User-Agent": get_random_user_agent(),
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                    }
                    response = make_request(show_url, headers=html_headers, follow_redirects=True)
                    if response.status_code == 200:
                        email_match = local_re.search(r'href="mailto:([^"]+)"', response.text)
                        if email_match:
                            extra["email"] = email_match.group(1).strip()
                except Exception:
                    pass
            if followers := data.get("followers"): extra["followers"] = str(followers)
            if following := data.get("following"): extra["following"] = str(following)
            if avatar_url := data.get("avatar_url"): extra["avatar"] = avatar_url
            if twitter := data.get("twitter_username"): extra["twitter"] = twitter
            if repos := data.get("public_repos"): extra["public_repos"] = str(repos)
            if created_at := data.get("created_at"): extra["created_at"] = created_at
            
            links = []
            if blog := data.get("blog"):
                links.append(blog)
            try:
                social_url = f"https://api.github.com/users/{user}/social_accounts"
                social_response = make_request(social_url, headers=headers, follow_redirects=True)
                if social_response.status_code == 200:
                    for item in social_response.json():
                        if u := item.get("url"):
                            links.append(u)
            except Exception:
                pass
            if links:
                unique_links = list(dict.fromkeys(links))
                extra["links"] = ", ".join(unique_links)
            
            return Result.taken(extra=extra, url=show_url)
            
        elif api_response.status_code == 404:
            return Result.available(url=show_url)
            
        # Fallback to HTML if API is rate-limited (403) or unavailable
        html_headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = make_request(show_url, headers=html_headers, follow_redirects=True)
        
        if response.status_code == 404:
            return Result.available(url=show_url)
        elif response.status_code == 200:
            extra = {}
            try:
                name_match = local_re.search(r'itemprop="name">\s*([^<\n\r]+)\s*</span>', response.text)
                if name_match: extra["name"] = name_match.group(1).strip()
                
                bio_match = local_re.search(r'class="p-note user-profile-bio[^"]*"[^>]*><div>([^<]+)</div>', response.text)
                if bio_match: extra["bio"] = bio_match.group(1).strip()
                
                company_match = local_re.search(r'itemprop="worksFor"[^>]*aria-label="Organization:\s*([^"]+)"', response.text)
                if company_match: extra["company"] = company_match.group(1).strip()
                
                loc_match = local_re.search(r'itemprop="homeLocation"[^>]*aria-label="Home location:\s*([^"]+)"', response.text)
                if loc_match: extra["location"] = loc_match.group(1).strip()
                
                li_matches = local_re.findall(r'<li\s+[^>]*itemprop="(url|social)"[^>]*>([\s\S]*?)</li>', response.text)
                links = []
                for item_type, li in li_matches:
                    href_match = local_re.search(r'href="([^"]+)"', li)
                    if href_match:
                        url_val = href_match.group(1).strip().replace("&amp;", "&")
                        links.append(url_val)
                        if item_type == "url":
                            extra["website"] = url_val
                if links:
                    unique_links = list(dict.fromkeys(links))
                    extra["links"] = ", ".join(unique_links)
                
                email_match = local_re.search(r'href="mailto:([^"]+)"', response.text)
                if email_match: extra["email"] = email_match.group(1).strip()
                
                followers_match = local_re.search(r'class="text-bold color-fg-default">([0-9.]+[kM]?)</span>\s*followers', response.text)
                if followers_match: extra["followers"] = followers_match.group(1)
                
                following_match = local_re.search(r'class="text-bold color-fg-default">([0-9.]+[kM]?)</span>\s*following', response.text)
                if following_match: extra["following"] = following_match.group(1)
                
                # Fixed avatar extraction (using meta tag instead of random images on page)
                avatar_match = local_re.search(r'<meta property=\"og:image\" content=\"([^\"]+)\"', response.text)
                if avatar_match: extra["avatar"] = avatar_match.group(1).replace("&amp;", "&")
                
                orgs = local_re.findall(r'data-hovercard-type="organization"[^>]*href="/([^/"]+)"', response.text)
                if orgs:
                    unique_orgs = list(dict.fromkeys(orgs))
                    extra["organizations"] = ", ".join(unique_orgs)
                    
            except Exception:
                pass
            return Result.taken(extra=extra, url=show_url)
        else:
            return Result.error(f"Unexpected status: {response.status_code}", url=show_url)
            
    except Exception as e:
        return Result.error(e, url=show_url)


