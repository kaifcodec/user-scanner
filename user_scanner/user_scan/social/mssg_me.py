from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_mssg_me(user: str) -> Result:
    url = f"https://mssg.me/{user}"

    def process(r):
        # Missing handles end on the site's explicit 404 template.
        if r.status_code == 404 and 'id="page_404"' in r.text:
            return Result.available()

        # Reserved routes use the main site's manifest, not a profile.
        if r.status_code == 200 and 'href="/manifest.webmanifest"' in r.text:
            return Result.available()

        # Published profiles use a separate profile-page manifest.
        if r.status_code == 200 and 'href="/favicons/site.webmanifest"' in r.text:
            return Result.taken()

        # Blocks and template changes must not become verdicts.
        return Result.error(f"Unexpected response: HTTP {r.status_code}")

    return generic_validate(url, process, show_url=url, follow_redirects=True)
