import re
import urllib.parse

from user_scanner.core.orchestrator import Result, generic_validate


def validate_ccm(user: str) -> Result:
    encoded_user = urllib.parse.quote(user)
    url = f"https://ccm.net/profile/user/{encoded_user}"
    show_url = f"https://ccm.net/profile/user/{encoded_user}"

    def process(response) -> Result:
        if response.status_code == 404:
            if (
                re.search(r"<title>.*?(?:404|erreur|not found).*?</title>", response.text, re.I)
                or "404" in response.text
            ):
                return Result.available()
            return Result.error("404 response received without expected error marker")

        if response.status_code == 200:
            m = re.search(
                r"<title>(?:Profil de\s+)?([^<']+?)(?:'s profile)?\s*-\s*CCM</title>",
                response.text,
            )
            if m and m.group(1).strip().lower() == user.lower():
                extra: dict[str, str] = {}
                s = re.search(r'pro_header__status">\s*<span>([^<]+)</span>', response.text)
                if s:
                    extra["status"] = s.group(1).strip()

                labels = [
                    ("Registration date", "joined"),
                    ("Gender", "gender"),
                    ("Location", "location"),
                    ("Birthday", "birthday"),
                    ("Website", "website"),
                    ("Contributions", "contributions"),
                ]
                for label, key in labels:
                    dd = re.search(
                        rf"<dt>{label}</dt>\s*<dd[^>]*>(.*?)</dd>",
                        response.text,
                        re.S,
                    )
                    if dd:
                        val = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", dd.group(1))).strip()
                        if val and val.lower() not in ("not entered", "n/a"):
                            extra[key] = val

                return Result.taken(extra=extra)

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, show_url=show_url, follow_redirects=True)
