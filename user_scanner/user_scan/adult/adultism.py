import re
from user_scanner.core.orchestrator import generic_validate, Result, make_request


def validate_adultism(user):
    url = f"https://www.adultism.com/profile/{user}"
    show_url = f"https://www.adultism.com/profile/{user}"

    def process(response):
        if response.status_code == 200:
            is_taken = (
                re.search(r'itemprop="name">\s*' + re.escape(user) + r'\s*</h1>', response.text, re.IGNORECASE) or
                re.search(r'<title>\s*' + re.escape(user) + r'\s*-\s*Adultism</title>', response.text, re.IGNORECASE) or
                re.search(r'title="' + re.escape(user) + r'"', response.text, re.IGNORECASE) or
                re.search(r'alt="' + re.escape(user) + r'"',
                          response.text, re.IGNORECASE)
            )
            if is_taken:
                extra = {}

                # Extract Avatar
                avatar_match = re.search(r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*profile-image', response.text, re.IGNORECASE) or \
                    re.search(
                        r'<img[^>]+class="[^"]*profile-image[^"]*"[^>]*src="([^"]+)"', response.text, re.IGNORECASE)
                if avatar_match and "defaults/member" not in avatar_match.group(1):
                    extra["image"] = avatar_match.group(1)

                # Extract Channel ID
                channel_match = re.search(
                    r'data-channel-id="(\d+)"', response.text, re.IGNORECASE)
                if channel_match:
                    extra["channel_id"] = channel_match.group(1)

                # Extract Birth date
                birthdate_match = re.search(
                    r'<meta[^>]+itemprop="birthDate"[^>]+content="([^"]+)"', response.text, re.IGNORECASE)
                if birthdate_match:
                    extra["birthdate"] = birthdate_match.group(1)

                # Extract Gender/Sex
                sex_match = re.search(
                    r'Sex:.*?<span[^>]*>\s*(.*?)\s*</span>', response.text, re.DOTALL | re.IGNORECASE)
                if sex_match:
                    cleaned_sex = re.sub(
                        r"\s+", " ", sex_match.group(1)).replace("&nbsp;", " ").strip()
                    extra["gender"] = cleaned_sex
                else:
                    gender_meta = re.search(
                        r'<meta[^>]+itemprop="gender"[^>]+content="([^"]+)"', response.text, re.IGNORECASE)
                    if gender_meta and gender_meta.group(1).strip():
                        extra["gender"] = gender_meta.group(1).strip()

                # Extract Age
                age_match = re.search(
                    r'Age:.*?<span[^>]*>\s*(.*?)\s*</span>', response.text, re.DOTALL | re.IGNORECASE)
                if age_match:
                    extra["age"] = re.sub(
                        r"\s+", " ", age_match.group(1)).strip()

                # Extract Location
                loc_match = re.search(
                    r'Location:.*?<span[^>]*>\s*(.*?)\s*</span>', response.text, re.DOTALL | re.IGNORECASE)
                if loc_match:
                    extra["location"] = re.sub(
                        r"\s+", " ", loc_match.group(1)).strip()
                else:
                    loc_meta = re.search(
                        r'<meta[^>]+itemprop="homeLocation"[^>]+content="([^"]+)"', response.text, re.IGNORECASE)
                    if loc_meta:
                        extra["location"] = loc_meta.group(1).strip()

                # Extract Last login
                login_match = re.search(
                    r'Last login:.*?<span[^>]*>(.*?)</span[^>]*>', response.text, re.DOTALL | re.IGNORECASE)
                if login_match:
                    val = login_match.group(1)
                    val = re.sub(r'<[^>]+>', '', val)
                    extra["last_login"] = re.sub(r"\s+", " ", val).strip()

                # Extract Registration date
                joined_match = re.search(
                    r'Member since:.*?<span[^>]*>\s*(.*?)\s*</span>', response.text, re.DOTALL | re.IGNORECASE)
                if joined_match:
                    extra["joined"] = re.sub(
                        r"\s+", " ", joined_match.group(1)).strip()

                # Extract Subscriber count (checking data-canonical first, then quantity)
                sub_match = re.search(
                    r'class="[^"]*subscriber-count[^"]*"[^>]*data-canonical="(\d+)"', response.text, re.IGNORECASE)
                if sub_match:
                    extra["subscribers"] = sub_match.group(1)
                else:
                    quantity_match = re.search(
                        r'subscriber-count.*?<span[^>]*class="[^"]*(?:quantity|value)[^"]*"[^>]*>([^<]+)</span>', response.text, re.DOTALL | re.IGNORECASE)
                    if quantity_match:
                        extra["subscribers"] = quantity_match.group(1).strip()
                    else:
                        sub_span = re.search(
                            r'subscriber-count.*?<span[^>]*>([^<]+)</span>', response.text, re.DOTALL | re.IGNORECASE)
                        if sub_span:
                            extra["subscribers"] = sub_span.group(1).strip()

                # Extract Badges (Verified/Premium)
                if "pc-verified" in response.text:
                    extra["verified"] = "True"
                if "pc-premium" in response.text:
                    extra["premium"] = "True"

                # Extract Description/Interests
                interests_match = re.search(
                    r'<div[^>]+itemprop="description"[^>]*>\s*(.*?)\s*</div>', response.text, re.DOTALL | re.IGNORECASE)
                if interests_match:
                    cleaned_interests = re.sub(
                        r"\s+", " ", interests_match.group(1)).strip()
                    extra["interests"] = cleaned_interests

                # Extract Comments
                comments_match = re.search(
                    r'<div class="comments">\s*<div[^>]*>Comments:</div>\s*(.*?)\s*</div>', response.text, re.DOTALL | re.IGNORECASE)
                if comments_match:
                    cleaned_comments = re.sub(
                        r"\s+", " ", comments_match.group(1)).strip()
                    extra["comments"] = cleaned_comments

                # Step 2: Fetch the friends page sequentially to extract exact friends count
                try:
                    friends_url = f"https://www.adultism.com/profile/{user}/friends"
                    friends_resp = make_request(friends_url, timeout=5.0)
                    if friends_resp.status_code == 200:
                        friends_count_match = re.search(
                            r'<li class="page item-count">(\d+)\s+items</li>', friends_resp.text, re.IGNORECASE)
                        if friends_count_match:
                            extra["friends_count"] = friends_count_match.group(
                                1)
                except Exception:
                    pass  # Keep going if friends page request fails

                return Result.taken(extra=extra, url=show_url)

        if response.status_code == 404 or "Page not found" in response.text:
            return Result.available(url=show_url)

        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url)
