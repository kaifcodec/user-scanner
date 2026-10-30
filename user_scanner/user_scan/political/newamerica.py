import html
import re
import urllib.parse

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result


def validate_newamerica(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://www.newamerica.org/our-people/{encoded_user}/"
    show_url = url

    def process(response) -> Result:
        if response.status_code == 200 and "Page not found" not in response.text:
            final_url = str(response.url)
            unquoted_final = urllib.parse.unquote(final_url).lower()
            user_lower = user.lower()
            if f"/people/{user_lower}/" in unquoted_final or f"/our-people/{user_lower}/" in unquoted_final:
                extra: dict[str, str] = {}
                name_match = re.search(r'<h1 class="header2-name"[^>]*>([^<]+)</h1>', response.text)
                if name_match:
                    extra["name"] = name_match.group(1).strip()

                role_match = re.search(r'<p class="[^"]*header2-role[^"]*"[^>]*>([^<]+)</p>', response.text)
                if role_match:
                    extra["role"] = html.unescape(role_match.group(1)).strip()

                bio_match = re.search(
                    r'<div class="[^"]*body1[^"]*"[^>]*>(.*?)</div>',
                    response.text,
                    re.DOTALL,
                )
                if bio_match:
                    clean_bio = re.sub(r"<[^>]+>", " ", bio_match.group(1))
                    clean_bio = re.sub(r"\s+", " ", html.unescape(clean_bio)).strip()
                    if clean_bio:
                        extra["bio"] = clean_bio

                return Result.taken(extra=extra, url=final_url)

        if "Page not found" in response.text or response.status_code == 404:
            return Result.available(url=show_url)

        return Result.error(f"Unexpected response body, status {response.status_code}")

    return impersonate_validate(
        url,
        process,
        show_url=show_url,
        impersonate="chrome",
        allow_redirects=True,
    )
