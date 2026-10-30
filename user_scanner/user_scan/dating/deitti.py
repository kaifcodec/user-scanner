from user_scanner.core.orchestrator import Result, generic_validate


def validate_deitti(user: str) -> Result:
    """Use Deitti.net's inline username check without submitting registration."""
    show_url = "https://www.deitti.net/tili/liity"
    if (
        not 3 <= len(user) <= 20
        or not any(char.isalpha() for char in user)
        or not all(char.isalpha() or char in "0123456789_.#!?() -" for char in user)
    ):
        return Result.error("Username must be 3-20 characters with letters/numbers/punctuation", url=show_url)

    def process(response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected validation status: {response.status_code}", url=show_url)
        try:
            data = response.json()
        except Exception:
            return Result.error("Failed to parse Deitti JSON response", url=show_url)

        if isinstance(data, dict):
            if data.get("isValid") is True and not data.get("error"):
                return Result.available(url=show_url)
            err = str(data.get("error", ""))
            if data.get("isValid") is False and ("jo käytössä" in err or "jo kaytossa" in err):
                return Result.taken(url=show_url)
            if "enimmäispituus" in err:
                return Result.error("Username must be at most 20 characters", url=show_url)
            if err:
                return Result.error(err, url=show_url)

        return Result.error("Unexpected username validation response", url=show_url)

    return generic_validate(
        "https://www.deitti.net/ajax/validate/username",
        process,
        method="POST",
        data={"validate": user},
        headers={"X-Requested-With": "XMLHttpRequest"},
        show_url=show_url,
    )
