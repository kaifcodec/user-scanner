import re
import xmlrpc.client
import httpx

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request


def validate_pypi(user: str) -> Result:
    """
    Validates a PyPI username and extracts:

    - display_name
    - email
    - packages_count
    - packages
    """

    if not re.match(r"^(?!_+$)[A-Za-z0-9._-]+$", user):
        return Result.error(
            "Username may only contain letters, numbers, periods, underscores, and hyphens, and cannot consist solely of underscores"
        )

    profile_url = f"https://pypi.org/user/{user}"
    xmlrpc_url = "https://pypi.org/pypi"
    user_agent = get_random_user_agent()

    extra = {
        "display_name": None,
        "email": None,
        "packages_count": 0,
        "packages": [],
    }

    #
    # XML-RPC lookup
    #
    try:
        payload = xmlrpc.client.dumps(
            (user,),
            methodname="user_packages",
        )

        response = make_request(
            xmlrpc_url,
            method="POST",
            content=payload,
            headers={
                "Content-Type": "text/xml",
                "User-Agent": user_agent,
            },
            http2=True,
        )

        if response.status_code != 200:
            return Result.error(
                f"XML-RPC endpoint returned status code: {response.status_code}",
                url=profile_url,
            )

        parsed = xmlrpc.client.loads(response.text)
        packages = parsed[0][0]

    except (httpx.ConnectError, httpx.TimeoutException) as err:
        return Result.error(
            f"Network transport error: {err}",
            url=profile_url,
        )

    except Exception as err:
        return Result.error(
            f"System error checking XML-RPC: {err}",
            url=profile_url,
        )

    if not isinstance(packages, list) or not packages:
        return Result.available(url=profile_url)

    package_names = sorted({package_name for _, package_name in packages})

    extra["packages_count"] = len(package_names)
    extra["packages"] = package_names

    #
    # Query package JSON API to extract author name & email as fallback
    #
    if package_names:
        name_candidate = None
        email_candidate = None
        for pkg in package_names:
            if name_candidate and email_candidate:
                break
            try:
                pkg_url = f"https://pypi.org/pypi/{pkg}/json"
                res = make_request(
                    pkg_url,
                    headers={"User-Agent": user_agent},
                    http2=True,
                )
                if res.status_code == 200:
                    info = res.json().get("info", {})
                    author = info.get("author")
                    author_email = info.get("author_email")
                    maintainer = info.get("maintainer")
                    maintainer_email = info.get("maintainer_email")

                    for email_field in (author_email, maintainer_email):
                        if email_field and "@" in email_field:
                            if "<" in email_field and ">" in email_field:
                                parts = email_field.split("<")
                                name_part = parts[0].strip()
                                email_part = parts[1].replace(">", "").strip()
                                if not name_candidate and name_part:
                                    name_candidate = name_part
                                if not email_candidate and email_part:
                                    email_candidate = email_part
                            elif not email_candidate:
                                email_candidate = email_field.strip()

                    # Fallbacks for names
                    if (
                        author
                        and author.strip().lower() != "none"
                        and not name_candidate
                    ):
                        name_candidate = author.strip()
                    if (
                        maintainer
                        and maintainer.strip().lower() != "none"
                        and not name_candidate
                    ):
                        name_candidate = maintainer.strip()
            except Exception:
                pass

        if name_candidate:
            extra["display_name"] = name_candidate
        if email_candidate:
            extra["email"] = email_candidate

    return Result.taken(
        url=profile_url,
        extra=extra,
    )
