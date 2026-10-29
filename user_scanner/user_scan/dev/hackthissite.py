import re

from user_scanner.core.orchestrator import generic_validate, Result


def validate_hackthissite(user: str) -> Result:
    url = f"https://www.hackthissite.org/user/view/{user}"

    def process(response):
        if response.status_code == 200:
            m = re.search(r"<title>Hack This Site :: View User: ([^<]+)</title>", response.text)
            if m and m.group(1).strip().lower() == user.lower():
                extra, media = {}, {}
                r = re.search(r"Rank:\s*([^<(\n]+?)\s*\((\d+)\s*Points\)", response.text)
                if r:
                    extra["rank"] = r.group(1).strip()
                    extra["points"] = r.group(2)
                s = re.search(r"Status:\s*([^<\n]+)<br", response.text)
                if s: extra["status"] = s.group(1).strip()
                bad = ("", "not entered", "none", "hidden", "http://")
                for label, key in [
                    ("UserID", "user_id"),
                    ("Joined", "joined"),
                    ("Last Login", "last_login"),
                    ("Last Active", "last_active"),
                    ("Location", "location"),
                    ("Website", "website"),
                    ("TimeZone", "timezone"),
                ]:
                    v = re.search(rf"<b>{label}:</b>\s*([^<]*)<br", response.text)
                    if v:
                        val = v.group(1).strip()
                        if val and val.lower() not in bad:
                            extra[key] = val
                av = re.search(
                    r'<img src="(/pages/user/avatar\.view\.php\?id=(\d+))"', response.text
                )
                if av and av.group(2) != "404":
                    media["avatar"] = f"https://www.hackthissite.org{av.group(1)}"
                return Result.taken(extra=extra, media=media)
            if "<title>Hack This Site</title>" in response.text:
                return Result.available()
        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=url)
