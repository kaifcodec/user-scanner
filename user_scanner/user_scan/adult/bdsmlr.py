import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_bdsmlr(user):
    user = user.replace(".", "")
    url = f"https://{user}.bdsmlr.com"
    show_url = f"https://{user}.bdsmlr.com"

    def process(response):
        if response.status_code == 200 and "login" in response.text:
            extra = {}

            # Extract blog title
            title_match = re.search(
                r"<title>(.*?)</title>", response.text, re.IGNORECASE)
            if title_match:
                title_val = title_match.group(1).strip()
                if title_val.lower() != "no title":
                    extra["fullname"] = title_val
                else:
                    extra["fullname"] = user.capitalize()

            # Extract avatar image (if not default)
            image_match = re.search(
                r'<meta\s+property="og:image"\s+content="([^"]+)"', response.text, re.IGNORECASE)
            if image_match and "default_avatar" not in image_match.group(1):
                extra["image"] = image_match.group(1).strip()

            # Extract description
            desc_match = re.search(
                r'<meta\s+property="og:description"\s+content="([^"]+)"', response.text, re.IGNORECASE)
            if desc_match:
                desc_val = desc_match.group(1).strip()
                if desc_val.lower() != "no description":
                    extra["bio"] = desc_val

            # Extract blog ID
            blog_id_match = re.search(
                r'/followersblogs/(\d+)', response.text, re.IGNORECASE)
            if blog_id_match:
                extra["blog_id"] = blog_id_match.group(1)

            return Result.taken(extra=extra, url=show_url)

        if "This blog doesn't exist." in response.text or response.status_code == 404:
            return Result.available(url=show_url)

        return Result.error(f"Unexpected response code/body: {response.status_code}", url=show_url)

    return generic_validate(url, process, show_url=show_url)
