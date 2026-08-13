import hashlib
import re

from user_scanner.core.orchestrator import Result, generic_validate, make_request


def validate_bdsmsingles(user: str) -> Result:
    url = f"https://www.bdsmsingles.com/members/{user}/"
    show_url = url

    def process(response):
        if response.status_code == 202:
            challenge = re.search(
                r'prefix="([0-9a-f]+)",win="(\d+)",diff=(\d+)', response.text
            )
            if not challenge or challenge.group(3) != "4":
                return Result.error("Unsupported browser challenge.", url=show_url)

            prefix, window, _ = challenge.groups()
            nonce = next(
                (
                    value
                    for value in range(1 << 20)
                    if hashlib.sha256(f"{prefix}{value}".encode())
                    .hexdigest()
                    .startswith("0000")
                ),
                None,
            )
            if nonce is None:
                return Result.error("Could not solve browser challenge.", url=show_url)

            response = make_request(url, cookies={"_jscp": f"{window}.{nonce}"})

        if response.status_code == 200 and "<title>Profile" in response.text:
            extra = {}
            media = {}

            # Headline
            headline_match = re.search(r"<h1>(.*?)</h1>", response.text)
            if headline_match:
                extra["headline"] = headline_match.group(1).strip()

            # Info / Orientation
            info_match = re.search(
                r"</h2>\s*<p>\s*(.*?)\s*</p>", response.text, re.DOTALL
            )
            if info_match:
                # Clean up multiple whitespaces
                cleaned_info = re.sub(r"\s+", " ", info_match.group(1)).strip()
                # strip out html tags like <b>
                cleaned_info = re.sub(r"<[^>]+>", "", cleaned_info)
                extra["orientation"] = cleaned_info

            # Avatar (if not default nophoto svg)
            avatar_match = re.search(
                r'src="(https://media\.bdsmsingles\.com/images/user_photo/[^"]+)"',
                response.text,
            )
            if avatar_match and "nophoto" not in avatar_match.group(1):
                media["image"] = avatar_match.group(1)

            # Table fields extraction
            def extract_table_field(field_name):
                # Search for field label followed by its value div
                pattern = rf"{field_name}</div>\s*<div style=\"[^\"]*width:\s*60%;[^\"]*\">\s*(.*?)\s*</div>"
                match = re.search(pattern, response.text, re.DOTALL | re.IGNORECASE)
                return match.group(1).strip() if match else None

            first_name = extract_table_field("First name")
            if first_name:
                extra["fullname"] = first_name

            sign = extract_table_field("Sign")
            if sign:
                extra["sign"] = sign

            body = extract_table_field("My Body Type Is")
            if body:
                extra["body_type"] = body

            height = extract_table_field("My Height Is")
            if height:
                extra["height"] = height

            ethnicity = extract_table_field("My Ethnicity Is")
            if ethnicity:
                extra["ethnicity"] = ethnicity

            return Result.taken(extra=extra, media=media, url=show_url)

        if response.status_code == 302 and response.headers.get("location") == "/":
            return Result.available(url=show_url)

        return Result.error(
            "Unexpected response body, report it via GitHub issues.", url=show_url
        )

    return generic_validate(url, process, show_url=show_url)
