import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_orcid(user: str) -> Result:
    """Validate a researcher on ORCID (orcid.org)."""
    url = "https://pub.orcid.org/v3.0/expanded-search/"
    show_url = f"https://orcid.org/orcid-search/search?searchQuery={user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + ORCID JSON response
        if response.status_code == 200 and "num-found" in response.text:
            try:
                data = json.loads(response.text)
                num_found = data.get("num-found", 0)

                if num_found == 0:
                    return Result.available(url=show_url)

                results = data.get("expanded-result", [])
                if results and isinstance(results, list):
                    first_record = results[0]
                    extra = {}

                    given = first_record.get("given-names") or ""
                    family = first_record.get("family-names") or ""
                    credit = first_record.get("credit-name") or ""
                    full_name = f"{given} {family}".strip() or credit
                    if full_name:
                        extra["name"] = full_name

                    if orcid_id := first_record.get("orcid-id"):
                        extra["orcid_id"] = str(orcid_id).strip()

                    institutions = first_record.get("institution-name", [])
                    if institutions and isinstance(institutions, list):
                        unique_inst = list(dict.fromkeys(institutions))[:3]
                        if unique_inst:
                            extra["institution"] = ", ".join(str(i) for i in unique_inst)

                    emails = first_record.get("email", [])
                    if emails and isinstance(emails, list):
                        extra["public_emails"] = ", ".join(str(e) for e in emails)

                    return Result.taken(extra=extra, url=show_url)
            except Exception:
                return Result.error("Failed to parse ORCID JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes or unhandled responses (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(
        url, process, headers=headers, show_url=show_url, follow_redirects=True,
        params={"q": user, "start": 0, "rows": 5},
    )
