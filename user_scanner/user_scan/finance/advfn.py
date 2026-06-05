from user_scanner.core.orchestrator import generic_validate, Result

import re as local_re

def validate_advfn(user):
    url = f"https://uk.advfn.com/forum/profile/{user}"
    show_url = url

    def process(response):
        if "Profile | ADVFN" in response.text:
            extra = {}
            html = response.text

            avatar_match = local_re.search(r'<img class="profile-pic" src="([^"]+)">', html)
            if avatar_match:
                url_src = avatar_match.group(1)
                if url_src.startswith("//"):
                    url_src = "https:" + url_src
                extra["avatar"] = url_src

            joined_match = local_re.search(r'<span class="registration">Member since:\s*([^<]+)</span>', html)
            if joined_match:
                extra["joined"] = joined_match.group(1).strip()

            sub_match = local_re.search(r'<p class="subscription">([^<]+)</p>', html)
            if sub_match:
                extra["subscription"] = sub_match.group(1).strip()

            posts_match = local_re.search(r'href="#posts"><span>(\d+)</span>Posts</a>', html)
            if posts_match:
                extra["posts"] = int(posts_match.group(1))

            followers_match = local_re.search(r'href="#followers"><span>(\d+)</span>Followers</a>', html)
            if followers_match:
                extra["followers"] = int(followers_match.group(1))

            following_match = local_re.search(r'href="#following"><span>(\d+)</span>Following</a>', html)
            if following_match:
                extra["following"] = int(following_match.group(1))

            about_match = local_re.search(r'<h2>About</h2>\s*(?:<div[^>]*>)?\s*<p>([\s\S]*?)</p>', html)
            if about_match:
                bio = about_match.group(1).strip()
                if "has no comment yet" not in bio.lower():
                    extra["bio"] = bio

            return Result.taken(extra=extra)

        if "ADVFN ERROR - Page Not Found" in response.text:
            return Result.available()

        return Result.error("Unexpected response body, report it via GitHub issues.")

    return generic_validate(url, process, show_url=show_url)

