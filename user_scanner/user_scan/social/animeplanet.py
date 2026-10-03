import html
import re
from urllib.parse import quote, urljoin, urlsplit

from user_scanner.core.impersonate import impersonate_validate
from user_scanner.core.result import Result

BASE_URL = "https://www.anime-planet.com"


def validate_animeplanet(user: str) -> Result:
    url = f"{BASE_URL}/users/{quote(user, safe='')}"

    def process(response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        if (
            str(response.url).rstrip("/") == f"{BASE_URL}/community"
            and "Be a part of the community" in response.text
        ):
            return Result.available()

        profile = re.search(
            r'id="profileName".*?<a href="/users/[^"]+">([^<]+)</a>',
            response.text,
            re.DOTALL,
        )
        if not profile or html.unescape(profile.group(1)).strip().casefold() != user.casefold():
            return Result.error("Unable to verify Anime-Planet profile")

        extra: dict[str, object] = {}
        media: dict[str, str] = {}

        for key, pattern in {
            "id": r"toggle_follow\((\d+)\)",
            "location": r'<i class="fa fa-home"></i>\s*([^<]+)</li>',
            "joined": r'<i class="fa fa-calendar"></i>\s*Joined\s+([^<]+)</li>',
            "last_online": r'id="profileName"[^>]*title="Last online ([^"]+)"',
            "followers": r'/followers">([\d,]+) Followers</a>',
            "following": r'/following">([\d,]+) Following</a>',
        }.items():
            if match := re.search(pattern, response.text):
                value = html.unescape(match.group(1)).strip()
                extra[key] = int(value.replace(",", "")) if key in {"id", "followers", "following"} else value

        if match := re.search(
            r'<i class="fa fa-user"></i>\s*([^<]+)</li>', response.text
        ):
            age, _, gender = html.unescape(match.group(1)).strip().partition(" / ")
            if age.isdigit():
                extra["age"] = int(age)
            if gender and gender != "?":
                extra["gender"] = gender

        for medium, state, count in re.findall(
            r'href="/users/[^"]+/(anime|manga)/([^"]+)"[^>]*>\s*'
            r'<span class="slCount">([\d,]+)</span>',
            response.text,
        ):
            state = state.replace("wantto", "want_to_").replace("wont", "wont_")
            extra[f"{medium}_{state}"] = int(count.replace(",", ""))

        if match := re.search(r'id="totalEps">([\d,]+)</i>', response.text):
            extra["anime_total_episodes"] = int(match.group(1).replace(",", ""))

        for medium, graph, total in re.findall(
            r"<h3>(Anime|Manga) ratings</h3>.*?"
            r'<ul class="statGraph[^"]*">(.*?)</ul>.*?'
            r'<p class="plr-total[^"]*">\s*([\d,]+)',
            response.text,
            re.DOTALL,
        ):
            prefix = medium.lower()
            extra[f"{prefix}_ratings"] = int(total.replace(",", ""))
            distribution = [
                f"{score}: {count}"
                for count, score in re.findall(
                    r'<li[^>]*title="([\d,]+)"[^>]*>.*?'
                    r"<span>([\d.]+)</span>",
                    graph,
                    re.DOTALL,
                )
            ]
            extra[f"{prefix}_rating_distribution"] = distribution

        for medium, duration in re.findall(
            r"<h2>Life on (anime|manga)</h2>.*?"
            r'<ul class="loa-labels[^"]*">(.*?)</ul>',
            response.text,
            re.DOTALL,
        ):
            parts = [
                f"{amount} {unit.lower()}"
                for amount, unit in re.findall(
                    r"<li[^>]*>\s*([\d,]+)\s*<span>([^<]+)</span>", duration
                )
                if int(amount.replace(",", ""))
            ]
            extra[f"{medium.lower()}_time"] = parts or ["0 minutes"]

        if match := re.search(
            r'href="(/forum/members/[^"]+\.(\d+))"', response.text
        ):
            extra["forum_profile"] = urljoin(BASE_URL, match.group(1))
            extra["forum_id"] = int(match.group(2))

        if match := re.search(
            r'<section class="[^"]*\bprofBio\b[^"]*">(.*?)</section>',
            response.text,
            re.DOTALL,
        ):
            bio = " ".join(
                html.unescape(re.sub(r"<[^>]+>", " ", match.group(1))).split()
            )
            if bio:
                extra["bio"] = bio
            if links := _external_links(match.group(1)):
                extra["links"] = links

        if match := re.search(r'id="user-avatar"[^>]*src="([^"]+)"', response.text):
            avatar = urljoin(BASE_URL, html.unescape(match.group(1)))
            if "/avatars/default/" not in avatar:
                media["avatar"] = avatar

        return Result.taken(extra=extra, media=media)

    return impersonate_validate(url, process, allow_redirects=True)


def _external_links(markup: str) -> list[str]:
    links: list[str] = []
    for raw_url in re.findall(r'<a[^>]+href=["\']([^"\']+)', markup):
        url = urljoin(BASE_URL, html.unescape(raw_url).strip())
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        if parsed.scheme not in {"http", "https", "mailto"}:
            continue
        if host == "anime-planet.com" or host.endswith(".anime-planet.com"):
            continue
        if url not in links:
            links.append(url)
    return links
