import html
import re
from urllib.parse import urlencode, urljoin

from user_scanner.core.orchestrator import Result, generic_validate

PROFILE_URL = "https://www.fredmiranda.com/forum/viewprofile.php"


def _text(markup: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def validate_fredmiranda(user: str) -> Result:
    show_url = f"{PROFILE_URL}?{urlencode({'Action': 'viewprofile', 'username': user})}"

    def process(response) -> Result:
        body = response.text

        if response.status_code != 200:
            return Result.error(f"Unexpected status code: {response.status_code}")

        if "<b>View Profile for Guest</b>" in body:
            return Result.available()

        heading = re.search(
            r"<font face=verdana,arial size=3 color=FFFFCC><b>\s*([^<]+?)\s*</b>",
            body,
        )
        if not heading or _text(heading.group(1)).casefold() != user.casefold():
            return Result.error("Profile response missing the expected username")

        extra: dict[str, str | bool | int | list[str]] = {}
        for key, label in (
            ("posts", r"Total\s+Posts"),
            ("likes", "Received Likes"),
            ("registered", "Registered"),
            ("country", "Country"),
            ("city", "City"),
        ):
            if match := re.search(rf"{label}:\s*(?:<a[^>]*>)?([^<]+)", body):
                extra[key] = _text(match.group(1))

        if status := re.search(
            r"<span[^>]*>(Online|Offline)</span>", body, re.IGNORECASE
        ):
            extra["online_status"] = status.group(1)

        if post_rank := re.search(
            r"<span title=['\"]([^'\"]*posts)['\"]", body, re.IGNORECASE
        ):
            extra["post_rank"] = _text(post_rank.group(1))

        if upload_sell := re.search(
            r"Upload (?:&amp;|&) Sell</a>:\s*<font[^>]*><b>(On|Off)</b>",
            body,
            re.IGNORECASE,
        ):
            extra["upload_sell"] = upload_sell.group(1)

        if feedback := re.search(
            r"Feedback Status:.*?<td[^>]*>([\d,-]+)<br>Great</td>"
            r"<td[^>]*>([\d,-]+)<br>Fair</td>"
            r"<td[^>]*>([\d,-]+)<br>Poor</td>",
            body,
            re.DOTALL,
        ):
            counts = [
                int(value.replace(",", "")) if value != "-" else 0
                for value in feedback.groups()
            ]
        elif re.search(r"<p class=['\"]text-white['\"]>\s*</p>", body):
            counts = [0, 0, 0]
        else:
            counts = None

        if counts is not None:
            extra.update(
                feedback_great=counts[0],
                feedback_fair=counts[1],
                feedback_poor=counts[2],
                feedback_total=sum(counts),
            )

        if user_id := re.search(
            r"(?:/forum/feedback/|viewtopuploads\.php\?User=|/forum/uavatars/u)(\d+)",
            body,
        ):
            extra["user_id"] = int(user_id.group(1))

        if role := re.search(
            r"<p>\s*<font[^>]*><b>([^<]+)</b></font><br>\s*"
            r"<a[^>]+class=['\"]linksubsc['\"]",
            body,
            re.IGNORECASE,
        ):
            extra["role"] = _text(role.group(1))

        for key, label in (
            ("assignment_wins", "Assignments top"),
            ("featured_thread_wins", "Featured Thread"),
        ):
            if wins := re.search(
                rf"{label} winner:</span>\s*<a[^>]*>(\d+)\s+times?</a>",
                body,
                re.IGNORECASE,
            ):
                extra[key] = int(wins.group(1))

        if "TOP 15</span>" in body:
            extra["top_15"] = True

        profile = re.findall(
            r"<font face=['\"]verdana['\"]\s+size=1>\s*(.*?)\s*</font>",
            body,
            re.DOTALL | re.IGNORECASE,
        )
        for key, block in zip(("bio", "gear"), profile):
            if value := _text(block):
                extra[key] = value

        if website := re.search(
            r"(?:https?://|www\.)\S+",
            str(extra.get("bio", "")),
            re.IGNORECASE,
        ):
            url = website.group().rstrip(".,;)")
            extra["website"] = url if "://" in url else f"https://{url}"

        social_profiles = []
        for link in re.findall(
            r"<a\s+href=['\"]((?:https?://|www\.)[^'\"]+)['\"][^>]*>\s*"
            r"<img[^>]+title=['\"]",
            body,
            re.IGNORECASE,
        ):
            link = html.unescape(link)
            social_profiles.append(link if "://" in link else f"https://{link}")
        if social_profiles:
            extra["social_profiles"] = social_profiles

        avatar = re.search(r'<img src="([^"]+)" width="60" height="60"', body)
        media = {}
        if avatar and "/forum/images/avatars/" not in (
            src := html.unescape(avatar.group(1))
        ):
            media["avatar"] = urljoin(PROFILE_URL, src)
        return Result.taken(extra=extra, media=media)

    return generic_validate(
        PROFILE_URL,
        process,
        params={"Action": "viewprofile", "username": user},
        show_url=show_url,
    )
