import html
import json
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import Result, generic_validate


def validate_jetpunk(user: str) -> Result:
    url = f"https://www.jetpunk.com/users/{quote(user, safe='')}"

    def process(response) -> Result:
        if (
            response.status_code == 404
            and "<h1>404 File Not Found</h1>" in response.text
        ):
            return Result.available()

        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        heading = re.search(r"<h1>(.*?)'s User Profile</h1>", response.text)
        if not heading or html.unescape(heading.group(1)).casefold() != user.casefold():
            return Result.error("Profile response did not match the requested username")

        extra: dict[str, object] = {
            label.replace(" ", "_"): value
            for value, label in re.findall(
                r"(?:</i>)?([\d,]+) (quiz takes|subscribers|day streak)</div>",
                response.text,
            )
        }

        marker = "var _page = "
        try:
            page = json.JSONDecoder().raw_decode(
                response.text.partition(marker)[2]
            )[0]["data"]
            if isinstance(user_id := page.get("subscribeUser"), int) and user_id > 0:
                extra["user_id"] = user_id
            countries = [
                country["name"]
                for country in page.get("countries", [])
                if country.get("checked") and country.get("name")
            ]
            if countries:
                extra["countries_visited"] = countries
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        quizzes = re.search(
            r"href='/user-quizzes/\d+'[^>]*>All Quizzes by .*? \(([\d,]+)\)",
            response.text,
        )
        if quizzes:
            extra["quizzes"] = quizzes.group(1)

        for key, pattern in (
            ("quizmaker_rank", r"maker-rank[^>]*><a[^>]*>#([\d,]+)</a>"),
            ("series", r"All Series by .*? \(([\d,]+)\)"),
            ("total_level", r"shield-total shield.*?level-num[^>]*>([\d,]+)</div>"),
            ("total_points", r"shield-total shield.*?level-points[^>]*>([\d,]+) points"),
        ):
            if match := re.search(pattern, response.text, re.DOTALL):
                extra[key] = match.group(1)

        word_stats = re.search(
            r"Words Found.*?Puzzles Played.*?Featured Played.*?Featured Completed"
            r".*?<tr>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>"
            r"\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>",
            response.text,
            re.DOTALL,
        )
        if word_stats:
            extra.update(
                zip(
                    ("words_found", "puzzles_played", "featured_played", "featured_completed"),
                    (value.strip() for value in word_stats.groups()),
                )
            )

        badges = re.findall(r"href=['\"]/badges/([^'\"]+)", response.text)
        if badges:
            extra["badges"] = badges

        levels = re.findall(
            r"shield-language[^>]*><a[^>]*>([^<]+)</a>.*?"
            r"level-num[^>]*>([\d,]+)</div>.*?"
            r"level-points[^>]*>([\d,]+) points</div>",
            response.text,
            re.DOTALL,
        )
        if levels:
            extra["language_levels"] = [
                f"{html.unescape(language)}: level {level} ({points} points)"
                for language, level, points in levels
            ]

        for key, path in (
            ("popular_quizzes", "user-quizzes"),
            ("popular_series", "series"),
        ):
            titles = re.findall(
                rf"quiz-row[^>]*><a href=['\"]/{path}/[^'\"]+['\"]>(.*?)</a>",
                response.text,
            )
            if titles:
                extra[key] = [html.unescape(title) for title in titles]

        return Result.taken(extra=extra)

    return generic_validate(url, process, show_url=url)
