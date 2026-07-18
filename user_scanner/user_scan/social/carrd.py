import re
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_carrd(user: str) -> Result:
    url = f"https://{user}.carrd.co"
    show_url = f"https://{user}.carrd.co"

    def process(r):
        if r.status_code == 404:
            return Result.available()

        if r.status_code == 200:
            if "Sorry, the requested page could not be found." in r.text or "Page not found" in r.text:
                return Result.available()

            extra = {}

            # Parse display name from h1
            h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", r.text)
            if h1_match:
                extra["display_name"] = h1_match.group(1).strip()
            else:
                title_match = re.search(r"<title>([^<]+)</title>", r.text)
                if title_match:
                    extra["display_name"] = title_match.group(1).strip()

            # Parse subtext (bio)
            bio_match = re.search(r'<p[^>]*class="[^"]*text[^"]*"[^>]*>([^<]+)</p>', r.text)
            if bio_match:
                extra["bio"] = bio_match.group(1).strip()

            # Parse image
            img_match = re.search(r'<img[^>]+src="([^"]+)"', r.text)
            if img_match:
                img_src = img_match.group(1).strip()
                if img_src.startswith("assets/"):
                    img_src = f"https://{user}.carrd.co/{img_src}"
                extra["avatar_url"] = img_src

            # Extract social links from anchor tags
            links = []
            for href in re.findall(r'<a[^>]+href="([^"]+)"', r.text):
                if any(domain in href for domain in ["twitter.com", "x.com", "instagram.com", "linkedin.com", "github.com", "youtube.com"]):
                    links.append(href)
            if links:
                extra["links"] = list(set(links))

            return Result.taken(extra=extra)

        return Result.error(f"HTTP {r.status_code}")

    return generic_validate(
        url, process, show_url=show_url, follow_redirects=True
    )
