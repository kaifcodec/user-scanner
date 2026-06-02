import re
from user_scanner.core.orchestrator import generic_validate, Result


def validate_zmarsa(user):
    url = f"https://zmarsa.com/uzytkownik/{user}"
    show_url = url

    def process(response):
        if "Statystyki" in response.text:
            extra = {}

            # Avatar image URL (if not default)
            avatar_match = re.search(
                r'src="(https://zmarsa.com/storage/avatar/[^"]+)"', response.text)
            if avatar_match and "default.jpg" not in avatar_match.group(1):
                extra["image"] = avatar_match.group(1)

            # Date joined
            joined_match = re.search(
                r"<p>Dołączył/a (.*?)</p>", response.text, re.IGNORECASE)
            if joined_match:
                extra["joined"] = joined_match.group(1).strip()

            # Stats (Points, Ranking, Followers, Following, Posts, Comments)
            points_match = re.search(
                r"Punkty:\s*<b>(.*?)</b>", response.text, re.IGNORECASE)
            if points_match:
                extra["points"] = points_match.group(1).strip()

            ranking_match = re.search(
                r"Pozycja w Rankingu:.*?<b>#(.*?)</b>", response.text, re.DOTALL | re.IGNORECASE)
            if ranking_match:
                extra["ranking"] = ranking_match.group(1).strip()

            followers_match = re.search(
                r"Obserwujących:\s*<b>(.*?)</b>", response.text, re.IGNORECASE)
            if followers_match:
                extra["followers"] = followers_match.group(1).strip()

            following_match = re.search(
                r"Obserwowani:\s*<b>(.*?)</b>", response.text, re.IGNORECASE)
            if following_match:
                extra["following"] = following_match.group(1).strip()

            posts_match = re.search(
                r"Dodanych postów:\s*<b>(.*?)</b>", response.text, re.IGNORECASE)
            if posts_match:
                extra["posts"] = posts_match.group(1).strip()

            comments_match = re.search(
                r"Dodanych komentarzy:\s*<b>(.*?)</b>", response.text, re.IGNORECASE)
            if comments_match:
                extra["comments"] = comments_match.group(1).strip()

            return Result.taken(extra=extra, url=show_url)

        if "<title>Error 404 - zMarsa.com<" in response.text:
            return Result.available(url=show_url)

        return Result.error("Unexpected response body, report it via GitHub issues.", url=show_url)

    return generic_validate(url, process, show_url=show_url)
