import base64
import json
import random
import re
import string

import httpx

from user_scanner.core.result import Result

SIGN_PATTERN = re.compile(
    r"""
    \s*function\(x\)\s*\{\s*try\s*\{\s*return\s*\[
    '([^'\\]*)',\s*x\.codePointAt\(0\)\s*\*\s*x\.length\s*\^\s*(\d+),
    \s*\[\s*([0-3]\s*,\s*[0-3]\s*,\s*[0-3]\s*,\s*[0-3])\s*\]\.map\(function\(i\)\s*\{\s*return\s*\[
    '([^'\\]*)','([^'\\]*)','([^'\\]*)','([^'\\]*)'
    \]\[i\]\s*\}\)\.join\(''\),\s*'([^'\\]*)'
    \]\.join\('\ '\)\s*;?\s*\}\s*catch\s*\(e\)\s*\{
    \s*return\s*'error'\s*;?\s*\}\s*\}\s*
""",
    re.VERBOSE,
)


def _js_length(value: str) -> int:
    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def _codepoints(value: str) -> list[int]:
    normalized = value.encode("utf-16-le", errors="surrogatepass").decode(
        "utf-16-le", errors="surrogatepass"
    )
    return [ord(char) for char in normalized]


def _int32(value: int) -> int:
    return (value + 2**31) % 2**32 - 2**31


def _compute_signed3(email: str, source: str) -> str:
    match = SIGN_PATTERN.fullmatch(source)
    if not match:
        raise ValueError("Format sign_fn non reconnu")
    prefix, mask, order, a, b, c, d, suffix = match.groups()
    fragments = (a, b, c, d)
    block = "".join(fragments[int(index.strip())] for index in order.split(","))
    points = _codepoints(email)
    product = points[0] * _js_length(email) if points else 0
    number = _int32(_int32(product) ^ _int32(int(mask)))
    return " ".join((prefix, str(number), block, suffix))


def _simulate_typing(user: dict) -> dict[str, list[str]]:
    profile = user.get("profile_attributes", {})
    values = {
        "email": user["email"],
        "username": profile.get("username"),
    }
    if profile.get("age") is not None:
        values["age"] = str(profile["age"])

    logs = {}
    for field, value in values.items():
        if not value:
            continue
        events, current = [], ""
        for char in str(value):
            events.append(char)
            current += char
            events.append(f">>{current}<<")
        if events:
            logs[field] = events
    return logs


def _encode_logs(logs: dict[str, list[str]]) -> str:
    joined = {field: "".join(events) for field, events in logs.items()}
    text = json.dumps(joined, ensure_ascii=False, separators=(",", ":"))
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _generate_age() -> int:
    """Génère un âge aléatoire compris entre 20 et 80 ans inclus."""
    return random.randint(20, 80)


def _generate_username() -> str:
    """Génère un nom d'utilisateur de 5 à 15 lettres ASCII."""
    length = random.randint(5, 15)
    return "".join(random.choices(string.ascii_letters, k=length))


def _generate_password() -> str:
    """
    Génère un mot de passe de 7 à 20 caractères contenant un mélange
    garanti de chiffres, de lettres minuscules et de lettres majuscules.
    """
    length = random.randint(7, 20)
    alphabet = string.ascii_letters + string.digits

    # Garantit au moins un caractère de chaque catégorie pour éviter un rejet du formulaire
    password_chars = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
    ]
    password_chars.extend(random.choices(alphabet, k=length - 3))
    random.shuffle(password_chars)

    return "".join(password_chars)


def _build_payload(email: str, sign_fn: str) -> dict:
    password = _generate_password()
    username = _generate_username()
    age = _generate_age()
    user_data = {
        "email": email,
        "password": password,
        "profile_attributes": {
            "gender": "Male",
            "username": username,
            "location": "Miami, FL, United States",
            "city_id": 1840015149,
            "country": "United States",
            "city": "Miami",
            "state": "FL",
            "latitude": "25.784",
            "longitude": "-80.2102",
            "country_code": "US",
            "age": age,
            "ethnicity": "White",
        },
    }
    logs = _simulate_typing(user_data)
    return {
        "user": user_data,
        "signed": _js_length(email) * _js_length(password),
        "signed2": sum(_codepoints(email + password)),
        "signed3": _compute_signed3(email, sign_fn),
        "changes": _encode_logs(logs),
    }


async def _check(email: str) -> Result:
    """
    Vérifie si une adresse e-mail est déjà enregistrée sur Secret Benefits
    en interrogeant le flux d'inscription en plusieurs étapes.
    """
    show_url = "https://www.secretbenefits.com"
    signup_url = f"{show_url}/signup/man"
    data_url = f"{show_url}/signup/data/man"
    submit_url = f"{show_url}/signup/submit"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        # "Connection": "keep-alive",
    }

    async with httpx.AsyncClient(
        http2=False, headers=headers, follow_redirects=True
    ) as client:
        try:
            # 1. Récupération des cookies de session sur la page d'inscription
            init_resp = await client.get(signup_url, timeout=15.0)
            if not init_resp.is_success:
                return Result.error(
                    f"Failed to access signup page: {init_resp.status_code}",
                    url=show_url,
                )

            # 2. Récupération de la fonction de signature dynamique (sign_fn)
            data_headers = {**headers, "accept": "application/json"}
            data_resp = await client.get(data_url, headers=data_headers, timeout=15.0)
            if not data_resp.is_success:
                return Result.error(
                    f"Failed to fetch signup data: {data_resp.status_code}",
                    url=show_url,
                )

            data_json = data_resp.json()
            sign_fn = data_json.get("sign_fn")
            if not isinstance(sign_fn, str):
                return Result.error("Missing sign_fn in signup data", url=show_url)

            # 3. Construction du payload JSON signé
            payload = _build_payload(email, sign_fn)

            # 4. Soumission du formulaire d'inscription
            post_headers = {
                **headers,
                "accept": "application/json, text/plain, */*",
            }
            response = await client.post(
                submit_url, headers=post_headers, json=payload, timeout=15.0
            )
            res_status = response.status_code
            res_text = response.text.lower()

            if res_status == 429:
                return Result.error(
                    "Rate limited; try using the '-d' flag", url=show_url
                )

            return Result.error(
                f"Unexpected response (status {res_status})", url=show_url
            )

        except Exception as exc:
            return Result.error(str(exc), url=show_url)


async def validate_secretbenefits(email: str) -> Result:
    """
    Validateur public utilisé par le mode email_scan de user-scanner.
    """
    return await _check(email)
