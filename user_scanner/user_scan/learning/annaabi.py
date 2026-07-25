from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result


def validate_annaabi(user: str) -> Result:
    show_url = "https://annaabi.ee"

    def process(response):
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        body = response.text
        taken = (
            'value="2" id="psname"' in body
            and "Selline kasutajanimi on juba võetud" in body
        )
        available = (
            'value="1" id="psname"' in body
            and "See kasutajanimi on vaba" in body
        )
        if taken != available:
            return Result.taken() if taken else Result.available()
        return Result.error("Unexpected response body")

    return generic_validate(
        f"{show_url}/register.php",
        process,
        params={"go": "1", "usernamecheck": user},
        show_url=show_url,
    )
