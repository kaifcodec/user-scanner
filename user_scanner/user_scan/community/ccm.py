import re

from user_scanner.core.orchestrator import generic_validate, Result


def validate_ccm(user: str) -> Result:
    url = f"https://ccm.net/profile/user/{user}"
    show_url = f"https://ccm.net/profile/user/{user}"

    def process(response):
        if response.status_code == 404:
            return Result.available()
        if response.status_code == 200:
            m = re.search(r"<title>Profil de ([^<]+) - CCM</title>", response.text)
            if m and m.group(1).strip().lower() == user.lower():
                extra = {}
                h = re.search(r'<a href="/profile/user/[^"]+">\s*([^<]+?)\s*</a>', response.text)
                if h: extra["username"] = h.group(1).strip()
                s = re.search(r'pro_header__status">\s*<span>([^<]+)</span>', response.text)
                if s: extra["status"] = s.group(1).strip()
                for label, key in [
                    ("Registration date", "joined"),
                    ("Gender", "gender"),
                    ("Location", "location"),
                    ("Birthday", "birthday"),
                    ("Website", "website"),
                    ("Contributions", "contributions"),
                ]:
                    dd = re.search(
                        rf"<dt>{label}</dt>\s*<dd[^>]*>(.*?)</dd>", response.text, re.S
                    )
                    if dd:
                        val = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", dd.group(1))).strip()
                        if val and val.lower() not in ("not entered", "n/a"):
                            extra[key] = val
                return Result.taken(extra=extra)
        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
