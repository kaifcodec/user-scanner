import re
import xmlrpc.client
from email.utils import getaddresses
from typing import Any

import httpx

from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

# Packages listed on the result, and the ones sampled for release metadata.
PACKAGE_SAMPLE = 5

# Release metadata names whoever published a package — a co-maintainer, a
# company, a mailing list — not necessarily the account it hangs off. The keys
# below keep that provenance, so nothing downstream reads an address here as
# the account holder's own mailbox or a name here as the account holder's name.
CONTACT_ROLES = ("author", "maintainer")


def validate_pypi(user: str) -> Result:
    """
    Validates a PyPI username and extracts:

    - packages_count
    - packages
    - author / author_email / maintainer / maintainer_email of those packages
    """

    if not re.match(r"^(?!_+$)[A-Za-z0-9._-]+$", user):
        return Result.error(
            "Username may only contain letters, numbers, periods, underscores, and hyphens, and cannot consist solely of underscores"
        )

    profile_url = f"https://pypi.org/user/{user}"
    xmlrpc_url = "https://pypi.org/pypi"
    user_agent = get_random_user_agent()

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
    sample = package_names[:PACKAGE_SAMPLE]

    extra: dict[str, Any] = {
        "packages_count": len(package_names),
        "packages": sample,
    }
    extra.update(_release_metadata(sample, user_agent))

    return Result.taken(
        url=profile_url,
        extra=extra,
    )


def _release_metadata(packages: list[str], user_agent: str) -> dict[str, str]:
    """Every distinct name and address the sampled packages credit.

    All of them, rather than the first one an alphabetical walk reaches: which
    co-publisher that lands on is an accident of package naming, and several
    names on one account is the thing worth seeing.
    """
    found: dict[str, list[str]] = {}

    for package in packages:
        info = _package_info(package, user_agent)
        for role in CONTACT_ROLES:
            _add(found, role, info.get(role))
            for name, address in _contacts(info.get(f"{role}_email")):
                _add(found, role, name)
                if "@" in address:
                    _add(found, f"{role}_email", address)

    return {key: ", ".join(values) for key, values in found.items()}


def _package_info(package: str, user_agent: str) -> dict[str, Any]:
    try:
        response = make_request(
            f"https://pypi.org/pypi/{package}/json",
            headers={"User-Agent": user_agent},
            http2=True,
        )
        if response.status_code != 200:
            return {}
        return response.json().get("info") or {}
    except Exception:
        return {}


def _contacts(value: object) -> list[tuple[str, str]]:
    """The ``Name <addr>`` pairs in a core metadata contact field, which may
    credit several people in one comma-separated string."""
    return [
        (name.strip(), address.strip())
        for name, address in getaddresses([str(value or "")])
    ]


def _add(found: dict[str, list[str]], key: str, value: object) -> None:
    """Record a value under ``key``, unless it is empty, a duplicate, or the
    literal ``None`` some releases ship where the field was left unset."""
    text = str(value or "").strip()
    if not text or text.lower() == "none":
        return
    values = found.setdefault(key, [])
    if text not in values:
        values.append(text)
