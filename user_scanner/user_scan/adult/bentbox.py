import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_bentbox(user):
    url = f"https://bentbox.co/{user}"
    show_url = f"https://bentbox.co/{user}"

    def process(response):
        if response.status_code == 200:
            if "user_bar" in response.text or "bentbox.co" in response.text:
                if "user is currently not available" in response.text:
                    return Result.available(url=show_url)

                extra = {}

                # Extract profile data from OpenGraph or Title tags
                title_match = re.search(
                    r'<meta\s+property="og:title"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if title_match:
                    fullname = title_match.group(1).replace(
                        "- BentBox Profile", "").replace("- BentBox", "").replace("on BentBox", "").strip()
                    extra["fullname"] = re.sub(
                        r'\(@[a-zA-Z0-9_-]+\)', '', fullname).strip()
                else:
                    t_tag = re.search(r"<title>(.*?)</title>",
                                      response.text, re.IGNORECASE)
                    if t_tag:
                        fullname = t_tag.group(1).replace(
                            "- BentBox Profile", "").replace("- BentBox", "").replace("on BentBox", "").strip()
                        extra["fullname"] = re.sub(
                            r'\(@[a-zA-Z0-9_-]+\)', '', fullname).strip()

                # Extract Alternate Name / Username
                username_match = re.search(r'"alternateName":\s*"([^"]+)"', response.text, re.IGNORECASE) or \
                    re.search(
                        r'<meta\s+property="profile:username"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if username_match:
                    extra["username"] = username_match.group(1).strip()

                # Extract Bio
                desc_match = re.search(
                    r'<meta\s+property="og:description"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if desc_match:
                    extra["bio"] = desc_match.group(1).strip()

                # Extract Avatar
                image_match = re.search(
                    r'<meta\s+property="og:image"\s+content="([^"]+)"', response.text, re.IGNORECASE)
                if image_match:
                    extra["image"] = image_match.group(1).strip()

                # Extract Identifier / User ID
                id_match = re.search(
                    r'"identifier":\s*"([^"]+)"', response.text, re.IGNORECASE)
                if id_match:
                    extra["profile_id"] = id_match.group(1).strip()

                # Extract Followers
                followers_match = re.search(
                    r'(\d+)\s+Followers', response.text, re.IGNORECASE)
                if not followers_match:
                    follow_action = re.search(
                        r'FollowAction".*?"userInteractionCount":\s*"(\d+)"', response.text, re.DOTALL | re.IGNORECASE)
                    if follow_action:
                        extra["followers"] = follow_action.group(1)
                else:
                    extra["followers"] = followers_match.group(1)

                # Extract Boxes (Posts)
                boxes_match = re.search(
                    r'<span class="stat-value">(\d+)</span>\s*<span class="stat-label">Boxes</span>', response.text, re.DOTALL | re.IGNORECASE)
                if not boxes_match:
                    write_action = re.search(
                        r'WriteAction".*?"userInteractionCount":\s*"(\d+)"', response.text, re.DOTALL | re.IGNORECASE)
                    if write_action:
                        extra["boxes"] = write_action.group(1)
                else:
                    extra["boxes"] = boxes_match.group(1)

                # Extract Videos
                videos_match = re.search(
                    r'<span class="stat-value">(\d+)</span>\s*<span class="stat-label">Video[s]?</span>', response.text, re.DOTALL | re.IGNORECASE)
                if videos_match:
                    extra["videos"] = videos_match.group(1)

                return Result.taken(extra=extra, url=show_url)

        if response.status_code in (403, 429):
            return Result.error(
                f"Rate limit / Cloudflare protection block (HTTP {response.status_code}). Run with residential proxy or active session cookies.",
                url=show_url
            )

        if "user is currently not available" in response.text or response.status_code == 404:
            return Result.available(url=show_url)

        return Result.error(f"Unexpected response code/body: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url)
