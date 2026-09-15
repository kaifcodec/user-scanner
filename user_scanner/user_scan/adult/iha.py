import html
import re
from urllib.parse import quote

import httpx

from user_scanner.core.orchestrator import generic_validate
from user_scanner.core.result import Result

FIELD_NAMES = {
    "Konto tüüp": "account_type",
    "Nimi": "name",
    "Sünniaeg": "birth_date",
    "Riik": "country",
    "Elukoht": "location",
    "Kodulinn": "hometown",
    "Kasv": "height_cm",
    "Kaal": "weight_kg",
    "Kehaehitus": "body_type",
    "Juuste värv": "hair_color",
    "Silmade värv": "eye_color",
    "Orientatsioon": "orientation",
    "Soovin tutvuda": "looking_for",
    "Soovitud vanus": "desired_age",
    "Tutvumise eesmärk": "intent",
    "Mina (me) oleme": "relationship_status",
    "Kas sa oled abielus?": "marital_status",
    "Kas sul on lapsi?": "children",
    "Keeled": "languages",
    "Haridus": "education",
    "Kool/Ülikool kus õppisin": "school",
    "Hobid": "hobbies",
    "Avalik e-maili aadress": "public_email",
    "Kas sa suitsetad?": "smoking",
    "Suhe alkoholi": "alcohol",
    "Suhe narkootikumidesse": "drug_use",
    "Sissetulek": "income",
    "Minu roll seksis": "sexual_role",
    "Kui tihti soovin seksida": "sexual_frequency",
    "Mind erutab": "turn_ons",
    "Kas sulle meeldib masturbeerida": "masturbation",
    "BDSM": "bdsm",
    "Liiklusvahend": "vehicle",
    "Mind jahutab maha": "turn_offs",
    "Muusika, mis meeldib": "favorite_music",
    "Minu magamistoast leiad": "bedroom_items",
    "Mis muudab minu jaoks seksi kvaliteetseks?": "sexual_preferences",
    "Lemmikraamat": "favorite_book",
    "Lemmikfilm": "favorite_movie",
    "Ametikoht": "occupation",
    "Minu ettekujutus ideaalsest esimesest kohtingust": "ideal_first_date",
    "Mida õppisin oma viimasest suhtest": "relationship_lessons",
}


def validate_iha(user: str) -> Result:
    username = user.strip()
    url = f"https://www.iha.ee/users/{quote(username, safe='')}"

    def process(response: httpx.Response) -> Result:
        if response.status_code != 200:
            return Result.error(f"Unexpected response status: {response.status_code}")

        match = re.search(
            r'<div class="member_username"[^>]*>\s*([^<]+)', response.text
        )
        if match:
            profile_user = html.unescape(match.group(1)).strip()
            if profile_user.casefold() != username.casefold():
                return Result.error(
                    "Profile response does not match the requested handle"
                )
            user_id = re.search(r'<form[^>]+(?:name|id)="_(\d+)"', response.text)
            extra = _fields(response.text)
            if user_id:
                extra["user_id"] = int(user_id.group(1))
            return Result.taken(
                extra=extra,
                media=_media(response.text, user_id.group(1) if user_id else None),
            )

        if re.search(
            r"<title>\s*Iha\.ee - Seksikate inimeste kohtumispaik\s*</title>",
            response.text,
        ) and (
            'id="online_list"' in response.text
            or "Sellist kasutajat ei leitud" in response.text
        ):
            return Result.available()

        return Result.error("Could not verify profile page")

    return generic_validate(url, process, show_url=url)


def _fields(page: str) -> dict[str, object]:
    pairs = re.findall(
        r'<div class="member_form_opt1">\s*<div[^>]*>(.*?)</div>\s*</div>\s*'
        r'<div class="member_form_opt2">\s*<div[^>]*>(.*?)</div>\s*</div>',
        page,
        re.DOTALL,
    )
    fields: dict[str, object] = {}
    for raw_label, raw_value in pairs:
        label = _text(raw_label)
        value = _text(raw_value)
        if label not in FIELD_NAMES or not value:
            continue
        field = FIELD_NAMES[label]
        if field == "birth_date":
            value = re.sub(r"\s+\(\d+\)$", "", value)
        fields[field] = value
    return fields


def _media(page: str, user_id: str | None) -> dict[str, str]:
    if not user_id:
        return {}
    photos = list(
        dict.fromkeys(
            html.unescape(url)
            for url in re.findall(r"https://img2\.iha\.ee/[^\"'? )]+", page)
            if f"/{user_id}e" in url
        )
    )
    if not photos:
        return {}
    return {
        "avatar": photos[0],
        **{f"photo_{index}": url for index, url in enumerate(photos[1:], 1)},
    }


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
