import json
from types import SimpleNamespace

from user_scanner.core.result import Status
from user_scanner.user_scan.shopping import yaga_co_za, yaga_ee


def _html(page_props):
    data = {"props": {"pageProps": page_props}}
    return (
        '<script id="__NEXT_DATA__" type="application/json">'
        f"{json.dumps(data)}"
        "</script>"
    )


def _mock_generic_validate(monkeypatch, module, response_text, status_code=200):
    def fake_generic_validate(url, process, **kwargs):
        response = SimpleNamespace(status_code=status_code, text=response_text)
        return process(response).update(url=kwargs.get("show_url"))

    monkeypatch.setattr(module, "generic_validate", fake_generic_validate)


def test_yaga_ee_taken(monkeypatch):
    body = _html(
        {
            "initialShop": {
                "id": 6276916,
                "activeSlug": "brandikas",
                "name": "Brandikas",
                "description": "Secondhand brand shop",
                "owner": {"firstName": "Shop", "lastName": "Owner"},
            }
        }
    )
    _mock_generic_validate(monkeypatch, yaga_ee, body)

    result = yaga_ee.validate_yaga_ee("brandikas")

    assert result.status == Status.TAKEN
    assert result.url == "https://www.yaga.ee/brandikas"
    assert result.extra["id"] == 6276916
    assert result.extra["name"] == "Brandikas"
    assert result.extra["description"] == "Secondhand brand shop"
    assert result.extra["owner_first_name"] == "Shop"
    assert result.extra["owner_last_name"] == "Owner"


def test_yaga_ee_available(monkeypatch):
    body = _html({"initialShop": None, "initialProducts": []})
    _mock_generic_validate(monkeypatch, yaga_ee, body)

    result = yaga_ee.validate_yaga_ee("missing-shop")

    assert result.status == Status.AVAILABLE


def test_yaga_ee_missing_next_data(monkeypatch):
    _mock_generic_validate(monkeypatch, yaga_ee, "<html></html>")

    result = yaga_ee.validate_yaga_ee("brandikas")

    assert result.status == Status.ERROR
    assert result.reason == "Could not find Next.js data"


def test_yaga_ee_malformed_next_data(monkeypatch):
    body = (
        '<script id="__NEXT_DATA__" type="application/json">'
        "{"
        "</script>"
    )
    _mock_generic_validate(monkeypatch, yaga_ee, body)

    result = yaga_ee.validate_yaga_ee("brandikas")

    assert result.status == Status.ERROR
    assert result.reason == "Could not parse Next.js data"


def test_yaga_ee_rejects_path_separator_before_request(monkeypatch):
    def fail_generic_validate(*args, **kwargs):
        raise AssertionError("generic_validate should not be called")

    monkeypatch.setattr(yaga_ee, "generic_validate", fail_generic_validate)

    result = yaga_ee.validate_yaga_ee("bad/user")

    assert result.status == Status.ERROR
    assert result.reason == "Username contains unsafe URL path characters"


def test_yaga_ee_allows_special_characters(monkeypatch):
    body = _html(
        {
            "initialShop": {
                "id": 123,
                "activeSlug": "shop.name@tag",
                "name": "Special Shop",
                "owner": {},
            }
        }
    )
    _mock_generic_validate(monkeypatch, yaga_ee, body)

    result = yaga_ee.validate_yaga_ee("shop.name@tag")

    assert result.status == Status.TAKEN
    assert result.url == "https://www.yaga.ee/shop.name%40tag"
    assert result.extra["name"] == "Special Shop"


def test_yaga_co_za_taken_shop_name(monkeypatch):
    body = _html(
        {
            "initialShop": {
                "id": 5017196,
                "activeSlug": "the2lifewardrobe",
                "name": "The Second Life Wardrobe",
                "owner": {},
            }
        }
    )
    _mock_generic_validate(monkeypatch, yaga_ee, body)

    result = yaga_co_za.validate_yaga_co_za("the2lifewardrobe")

    assert result.status == Status.TAKEN
    assert result.url == "https://www.yaga.co.za/the2lifewardrobe"
    assert result.extra["id"] == 5017196
    assert result.extra["name"] == "The Second Life Wardrobe"
