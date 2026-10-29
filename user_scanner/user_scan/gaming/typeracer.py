import re

from user_scanner.core.orchestrator import generic_validate, Result


def validate_typeracer(user: str) -> Result:
    url = "https://data.typeracer.com/pit/profile"
    show_url = f"https://data.typeracer.com/pit/profile?user={user}"

    def process(response):
        if response.status_code == 200:
            m = re.search(
                r"<title>([^<(]+) \(([^)]+)\) \(TypeRacer Profile\)</title>",
                response.text,
            )
            if m and m.group(2).strip().lower() == user.lower():
                extra, media = {}, {}
                extra["fullname"] = m.group(1).strip()
                stats = {
                    "Full Avg.": "avg_wpm",
                    "Best Race": "best_wpm",
                    "Races": "races",
                    "WPM %": "wpm_percentile",
                    "Skill Level": "skill_level",
                    "Exp Level": "exp_level",
                }
                for value, label in re.findall(
                    r'Stat__Top">\s*([^<]+?)\s*</span>\s*'
                    r'<span class="Stat__Btm">([^<]+)',
                    response.text,
                ):
                    key = stats.get(label.strip())
                    if key:
                        extra[key] = value.strip()
                s = re.search(r"Racing Since:</span>\s*<span>([^<]+)</span>", response.text)
                if s: extra["racing_since"] = s.group(1).strip()
                s = re.search(r"Location:</span>\s*<span>\s*(\S[^<]*?)\s*</span>", response.text)
                if s: extra["location"] = s.group(1).strip()
                p = re.search(r'class="Plan__(Basic|Premium)"', response.text)
                if p: extra["plan"] = p.group(1).lower()
                s = re.search(
                    r"profileCar[\s\S]*?url\([\"'](/public/images/avatars/[^)\"']+)",
                    response.text,
                )
                if s:
                    media["avatar"] = f"https://data.typeracer.com{s.group(1)}"
                return Result.taken(extra=extra, media=media)
            if "Profile Not Found (TypeRacer Pit Stop)" in response.text:
                return Result.available()
        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, params={"user": user})
