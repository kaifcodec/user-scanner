import re
import html
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, generic_validate


def validate_admireme_vip(user):
    url = f"https://admireme.vip/{user}/"
    show_url = f"https://admireme.vip/{user}/"

    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def process(response):
        if "creator-stat subscriber" in response.text or response.status_code == 200:
            if "creator-stat subscriber" in response.text or "admireme.vip" in response.text:
                extra = {}

                # Extract Display Name/Title
                title_match = re.search(
                    r'<meta\s+property="og:title"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if title_match:
                    extra["fullname"] = title_match.group(
                        1).replace("| AdmireMe.VIP", "").strip()
                else:
                    t_tag = re.search(r"<title>(.*?)</title>",
                                      response.text, re.IGNORECASE)
                    if t_tag:
                        extra["fullname"] = t_tag.group(1).replace(
                            "| AdmireMe.VIP", "").strip()

                if "fullname" not in extra or not extra["fullname"]:
                    name_match = re.search(
                        r'class="name">\s*(.*?)\s*</h4>', response.text, re.IGNORECASE)
                    if name_match:
                        extra["fullname"] = html.unescape(
                            name_match.group(1)).strip()

                # Extract Username/Tag
                tag_match = re.search(
                    r'class="tag">\s*&#64;(.*?)\s*</h4>', response.text, re.IGNORECASE)
                if tag_match:
                    extra["username"] = html.unescape(
                        tag_match.group(1)).strip()

                # Extract Bio
                desc_match = re.search(
                    r'<meta\s+property="og:description"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if desc_match:
                    extra["bio"] = desc_match.group(1).strip()
                else:
                    bio_match = re.search(
                        r'<div class="bio">.*?<div class="inner">\s*(.*?)\s*</div>', response.text, re.DOTALL | re.IGNORECASE)
                    if bio_match:
                        cleaned_bio = re.sub(
                            r'<[^>]+>', ' ', bio_match.group(1))
                        cleaned_bio = re.sub(r'\s+', ' ', cleaned_bio)
                        extra["bio"] = html.unescape(cleaned_bio).strip()

                # Extract Avatar / Profile Image
                image_match = re.search(
                    r'<meta\s+property="og:image"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if image_match:
                    extra["image"] = image_match.group(1).strip()
                else:
                    bg_video_match = re.search(
                        r'class="profile_video"[^>]*style="[^"]*background-image:\s*url\(\s*\'?([^\')]+)\'?\s*\)', response.text, re.IGNORECASE)
                    if bg_video_match:
                        extra["image"] = bg_video_match.group(1).strip()
                    else:
                        bg_pic_match = re.search(
                            r'class="profile-pic[^"]*"[^>]*style="[^"]*background-image:\s*url\(\s*\'?([^\')]+)\'?\s*\)', response.text, re.IGNORECASE)
                        if bg_pic_match:
                            extra["image"] = bg_pic_match.group(1).strip()
                        else:
                            img_tag_match = re.search(
                                r'class="profile-pic[^"]*".*?<img[^>]+src="([^"]+)"', response.text, re.DOTALL | re.IGNORECASE)
                            if img_tag_match:
                                extra["image"] = img_tag_match.group(1).strip()

                # Extract Banner Image
                banner_match = re.search(
                    r'id="banner".*?<img[^>]+src="([^"]+)"', response.text, re.DOTALL | re.IGNORECASE)
                if banner_match:
                    extra["banner"] = banner_match.group(1).strip()

                # Extract Subscription Price
                price_match = re.search(
                    r'id="id-subscription-price-orig"\s+value="([^"]+)"', response.text, re.IGNORECASE)
                if price_match:
                    extra["price"] = html.unescape(
                        price_match.group(1)).strip()

                # Extract Post Counts
                teaser_posts = re.search(
                    r'class="[^"]*teaser[^"]*".*?<span class="number">(\d+)</span>', response.text, re.DOTALL | re.IGNORECASE)
                sub_posts = re.search(
                    r'class="[^"]*subscriber[^"]*".*?<span class="number">(\d+)</span>', response.text, re.DOTALL | re.IGNORECASE)
                t_count = 0
                s_count = 0
                if teaser_posts:
                    extra["teaser_posts"] = teaser_posts.group(1)
                    t_count = int(teaser_posts.group(1))
                if sub_posts:
                    extra["subscriber_posts"] = sub_posts.group(1)
                    s_count = int(sub_posts.group(1))
                if t_count or s_count:
                    extra["posts"] = str(t_count + s_count)

                return Result.taken(extra=extra, url=show_url)

        if response.status_code == 404 or "<title>Page Not Found |" in response.text:
            return Result.available(url=show_url)

        return Result.error(f"Unexpected status: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url, headers=headers)
