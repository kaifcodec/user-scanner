from user_scanner.core.helpers import ScanConfig
from user_scanner.core.result import Result, Status


def test_status_labels():
    assert Status.TAKEN.to_label(is_email=False) == "Found"
    assert Status.AVAILABLE.to_label(is_email=False) == "Not Found"
    assert Status.ERROR.to_label() == "Error"

    assert Status.TAKEN.to_label(is_email=True) == "Registered"
    assert Status.AVAILABLE.to_label(is_email=True) == "Not Registered"

    assert str(Status.TAKEN) == "Found"
    assert str(Status.AVAILABLE) == "Not Found"


def test_equality():
    taken = Result.taken()
    assert taken == taken
    assert taken == Result.taken()
    assert taken == Status.TAKEN
    assert taken == 0
    assert taken.__eq__("string_type") == NotImplemented

    available = Result.available()
    assert available == Result.available()
    assert available == Status.AVAILABLE
    assert available == 1

    error = Result.error()
    assert error == Status.ERROR
    assert error == 2

    skipped = Result.skipped()
    assert skipped == Status.SKIPPED
    assert skipped == 3


def test_get_reason_and_humanize():
    assert Result.available().get_reason() == ""
    assert Result.available("manual reason").get_reason() == "manual reason"

    assert (
        "Could not resolve hostname"
        in Result.error(Exception("Error 11001")).get_reason()
    )
    assert (
        "Connection closed by remote server"
        in Result.error(Exception("Error 10054")).get_reason()
    )

    assert (
        Result.available(Exception("some error")).get_reason()
        == "Exception: Some error"
    )


def test_has_reason():
    assert not Result.available().has_reason()
    assert Result.available("Has reason").has_reason()
    assert not Result.taken().has_reason()
    assert Result.taken("Has reason").has_reason()
    assert not Result.error().has_reason()
    assert Result.error("Has reason").has_reason()

def test_to_number():
    assert Result.error().to_number() == 2
    assert Result.available().to_number() == 1
    assert Result.taken().to_number() == 0


def test_from_number():
    assert Result.from_number(0) == Status.TAKEN
    assert Result.from_number(1) == Status.AVAILABLE
    assert Result.from_number(2) == Status.ERROR
    assert Result.from_number(3) == Status.SKIPPED

    for i in [-2, -1, 4, 5, 6, 7, 8, 9, 10]:
        assert Result.from_number(i) == Status.ERROR


def test_number_roundtrip():
    a = Result.available()
    assert Result.from_number(a.to_number()) == a
    b = Result.taken()
    assert Result.from_number(b.to_number()) == b
    c = Result.error()
    assert Result.from_number(c.to_number()) == c


def test_update_and_fields():
    res = Result.available()
    assert res.username is None
    assert res.url == ""

    res.update(
        username="alice",
        site_name="GitHub",
        category="Social",
        url="https://github.com/alice",
        is_email=False,
    )

    assert res.username == "alice"
    assert res.site_name == "GitHub"
    assert res.category == "Social"
    assert res.url == "https://github.com/alice"


def test_output_formats():
    res = Result.taken(
        username="testuser",
        site_name="Example",
        category="Tech",
        url="https://example.com/user",
    )

    d = res.as_dict()
    assert d["url"] == "https://example.com/user"
    assert d["status"] == "Found"

    assert res.to_csv() == "testuser,Tech,Example,Found,https://example.com/user,"

    json_std = res.to_json()
    assert '"username": "testuser"' in json_std
    assert '"url": "https://example.com/user"' in json_std

    res.update(is_email=True)
    json_email = res.to_json()
    assert '"email": "testuser"' in json_email
    assert '"username":' not in json_email


def test_console_output_and_show_url():
    conf = ScanConfig()
    v_conf = ScanConfig(verbose=True)

    res = Result.taken(site_name="MySite", url="https://mysite.com/u")

    out_hidden = res.get_console_output(conf)
    assert "[✔]" in out_hidden
    assert "Found" in out_hidden
    assert "https://mysite.com" not in out_hidden

    out_visible = res.get_console_output(v_conf)
    assert "[https://mysite.com/u]" in out_visible

    res_skip = Result.skipped(site_name="PrivacySite")
    output = res_skip.get_console_output(conf)
    assert "[~]" in output
    assert "Skipped" in output


def test_debug_string():
    res = Result.available(username="dev", url="http://dev.link")
    debug_str = res.debug()
    assert 'url: "http://dev.link"' in debug_str
    assert "status: Not Found" in debug_str
