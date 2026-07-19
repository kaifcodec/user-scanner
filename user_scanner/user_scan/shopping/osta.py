import html
import re
from urllib.parse import quote

from user_scanner.core.orchestrator import generic_validate, make_request
from user_scanner.core.result import Result

BASE_URL = "https://www.osta.ee"


def validate_osta(user: str) -> Result:
    url = (
        f"{BASE_URL}/en?fuseaction=listing.seller&q%5Bseller%5D="
        f"{quote(user, safe='')}"
    )

    def process(response):
        if response.status_code == 404:
            return Result.available()

        if response.status_code == 200 and re.search(
            rf'<strong class="username[^"]*">\s*{re.escape(user)}\s*</strong>',
            response.text,
            re.IGNORECASE,
        ):
            extra = _extract_profile(response.text)
            profile_url = (
                f"{BASE_URL}/en/user/{user_id}"
                if (user_id := _user_id(response.text))
                else ""
            )
            if profile_url:
                extra.update(_fetch(profile_url, _extract_profile) or {})
                about_url = f"{BASE_URL}/en?fuseaction=listing.aboutseller&user={user_id}"
                if (about := _fetch(about_url, _extract_about)) is not None:
                    extra.update(about)
            return Result.taken(extra=extra, url=profile_url)

        return Result.error(f"Unexpected response status: {response.status_code}")

    return generic_validate(url, process, follow_redirects=True)


def _user_id(html_text: str) -> str | None:
    match = re.search(r'href=["\'][^"\']*/(?:en/)?user/(\d+)', html_text, re.IGNORECASE)
    return match.group(1) if match else None


def _fetch(url: str, extract):
    try:
        response = make_request(url, follow_redirects=True)
        return extract(response.text) if response.status_code == 200 else None
    except Exception:
        return None


def _extract_profile(html_text: str) -> dict:
    text = _text(html_text)
    extra = {}

    business = re.search(
        r'<div[^>]*class="[^"]*user-business-auth[^"]*"[^>]*>(.*?)</div>',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    if business and re.search(r"\bCompany\b", _text(business.group(1)), re.IGNORECASE):
        extra["company"] = True
    if re.search(r'class="[^"]*id-card-logo-short', html_text, re.IGNORECASE):
        extra["identified"] = True

    if membership := re.search(
        r"User since\s+(\d{2}\.\d{2}\.\d{4}|\d{4})",
        text,
        re.IGNORECASE,
    ):
        extra["member_since"] = membership.group(1)

    fields = (
        (r"([\d,.]+)\s+Successful sales per year\b", "successful_sales_per_year"),
        (r"([\d,.]+)\s+Followers\b", "followers"),
        (r"([\d,.]+)\s+Active sales\b", "active_sales"),
        (r"\bFeedback\s+([\d,.]+)", "feedback_total"),
    )
    for pattern, key in fields:
        if match := re.search(pattern, text, re.IGNORECASE):
            extra[key] = _count(match.group(1))

    feedback = re.search(
        r"Feedback\s+positive\s+neutral\s+negative\b.*?\bAll\s+"
        r"([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)",
        text,
        re.IGNORECASE,
    )
    if feedback:
        extra.update(
            feedback_positive=_count(feedback.group(1)),
            feedback_neutral=_count(feedback.group(2)),
            feedback_negative=_count(feedback.group(3)),
        )

    avatar = re.search(
        r'class="[^"]*user-avatar[^"]*"[^>]*style="[^"]*'
        r"background-image:\s*url\(['\"]?([^'\")]+)",
        html_text,
        re.IGNORECASE,
    )
    if avatar:
        extra["avatar"] = html.unescape(avatar.group(1))

    return extra


def _extract_about(html_text: str) -> dict | None:
    if not re.search(r'class="[^"]*seller-profile-box', html_text, re.IGNORECASE):
        return None

    extra = {}

    for role, key in (
        ("seller", "seller_reliability"),
        ("bidder", "buyer_reliability"),
    ):
        rating = re.search(
            rf'class="[^"]*{role}-rating[^"]*"[^>]*>\s*'
            rf'(?:<span[^>]*>\s*)?<b[^>]*>\s*(\d+(?:\.\d+)?%)',
            html_text,
            re.IGNORECASE,
        )
        if rating:
            extra[key] = rating.group(1)

    meta = re.search(
        r'<div[^>]*class="[^"]*seller-meta-info[^"]*"[^>]*>(.*?)</div>',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    if meta:
        meta_text = _text(meta.group(1))
        if name := re.match(r"(.+?)\s*\|\s*User since\b", meta_text, re.IGNORECASE):
            extra["company_name"] = name.group(1).strip()
        if registration := re.search(r"\bReg\.\s*code:\s*([^|\s]+)", meta_text, re.IGNORECASE):
            extra["registration_code"] = registration.group(1)

    description = re.search(
        r'<div[^>]*id="show-profile-descr"[^>]*>.*?'
        r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    if description and (value := _text(description.group(1))):
        extra["description"] = value

    return extra


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _count(value: str) -> int:
    return int(re.sub(r"\D", "", value))
