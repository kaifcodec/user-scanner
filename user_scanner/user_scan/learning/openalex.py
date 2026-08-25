import json
from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_openalex(user: str) -> Result:
    """Validate a researcher/author on OpenAlex (openalex.org)."""
    url = "https://api.openalex.org/authors"
    show_url = f"https://openalex.org/authors?search={user}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    def process(response):
        # 1. Explicit check for not-found HTTP status
        if response.status_code == 404:
            return Result.available(url=show_url)

        # 2. Explicit verification of 200 OK + OpenAlex JSON response
        if response.status_code == 200 and "meta" in response.text:
            try:
                data = json.loads(response.text)
                count = data.get("meta", {}).get("count", 0)

                if count == 0:
                    return Result.available(url=show_url)

                results = data.get("results", [])
                if results and isinstance(results, list):
                    top_author = results[0]
                    extra = {}

                    if display_name := top_author.get("display_name"):
                        extra["name"] = str(display_name).strip()
                    if orcid := top_author.get("orcid"):
                        extra["orcid"] = str(orcid).strip()
                    if works_cnt := top_author.get("works_count"):
                        extra["works_count"] = str(works_cnt)
                    if cited_cnt := top_author.get("cited_by_count"):
                        extra["citations"] = str(cited_cnt)

                    institutions = top_author.get("last_known_institutions") or top_author.get("affiliations")
                    if institutions and isinstance(institutions, list):
                        inst_name = institutions[0].get("display_name") or institutions[0].get("institution", {}).get("display_name")
                        if inst_name:
                            extra["institution"] = str(inst_name).strip()

                    return Result.taken(extra=extra, url=show_url)
            except Exception:
                return Result.error("Failed to parse OpenAlex JSON response", url=show_url)

        # 3. Graceful error for unexpected status codes or unhandled responses (No bare else!)
        return Result.error(f"Unexpected response status: {response.status_code}", url=show_url)

    return generic_validate(
        url, process, headers=headers, show_url=show_url, follow_redirects=True,
        params={"filter": f"display_name.search:{user}"},
    )
