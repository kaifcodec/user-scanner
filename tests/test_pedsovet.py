from types import SimpleNamespace

from user_scanner.core.result import Status
from user_scanner.user_scan.other import pedsovet


def _profile_html(username="asd"):
    return f"""
    <html>
      <body>
        <div class="user">
          <center><img src="//pedsovet.su/default2.png" border="0"></center>
        </div>
        <div class="userinfo">
          <p>Логин: {username}</p>
          <p>Группа пользователей: Зарегистрированные </p>
          <p>Ссылка на профиль:<br><a href="//pedsovet.su/index/8-1876">pedsovet.su/index/8-1876</a></p>
          <p>Регистрация: Понедельник, 15.09.2008, 23:34</p>
        </div>
        <div class="block50 rightb"><span>Последний вход Понедельник, 15.09.2008, 23:34</span></div>
        <div class="osebe">О себе</div><div class="line1"></div>
        <p class="clr">Teacher profile</p>
        <div id="myCertificates"><certificates user-id='1876'></certificates></div>
      </body>
    </html>
    """


def _mock_generic_validate(monkeypatch, response_text, status_code=200):
    def fake_generic_validate(url, process, **kwargs):
        response = SimpleNamespace(status_code=status_code, text=response_text)
        return process(response).update(url=kwargs.get("show_url"))

    monkeypatch.setattr(pedsovet, "generic_validate", fake_generic_validate)


def test_pedsovet_taken(monkeypatch):
    _mock_generic_validate(monkeypatch, _profile_html())

    result = pedsovet.validate_pedsovet("asd")

    assert result.status == Status.TAKEN
    assert result.url == "https://pedsovet.su/index/8-0-asd"
    assert result.extra["id"] == "1876"
    assert result.extra["login"] == "asd"
    assert result.extra["group"] == "Зарегистрированные"
    assert result.extra["registered"] == "Понедельник, 15.09.2008, 23:34"
    assert result.extra["last_login"] == "Понедельник, 15.09.2008, 23:34"
    assert result.extra["avatar"] == "https://pedsovet.su/default2.png"
    assert result.extra["profile_url"] == "https://pedsovet.su/index/8-1876"
    assert result.extra["about"] == "Teacher profile"


def test_pedsovet_available(monkeypatch):
    _mock_generic_validate(monkeypatch, "Пользователь не найден")

    result = pedsovet.validate_pedsovet("missing_user")

    assert result.status == Status.AVAILABLE


def test_pedsovet_login_match_is_case_insensitive(monkeypatch):
    _mock_generic_validate(monkeypatch, _profile_html("Test"))

    result = pedsovet.validate_pedsovet("test")

    assert result.status == Status.TAKEN
    assert result.extra["login"] == "Test"


def test_pedsovet_rejects_period_before_request(monkeypatch):
    def fail_generic_validate(*args, **kwargs):
        raise AssertionError("generic_validate should not be called")

    monkeypatch.setattr(pedsovet, "generic_validate", fail_generic_validate)

    result = pedsovet.validate_pedsovet("bad.user")

    assert result.status == Status.ERROR
    assert "Usernames can only contain" in result.reason


def test_pedsovet_rejects_dash_before_request(monkeypatch):
    def fail_generic_validate(*args, **kwargs):
        raise AssertionError("generic_validate should not be called")

    monkeypatch.setattr(pedsovet, "generic_validate", fail_generic_validate)

    result = pedsovet.validate_pedsovet("bad-user")

    assert result.status == Status.ERROR
    assert "Usernames can only contain" in result.reason


def test_pedsovet_allows_at_sign(monkeypatch):
    _mock_generic_validate(monkeypatch, _profile_html("test@user"))

    result = pedsovet.validate_pedsovet("test@user")

    assert result.status == Status.TAKEN
    assert result.url == "https://pedsovet.su/index/8-0-test@user"
    assert result.extra["login"] == "test@user"


def test_pedsovet_ambiguous_page_errors(monkeypatch):
    _mock_generic_validate(monkeypatch, "<html><body>Педсовет</body></html>")

    result = pedsovet.validate_pedsovet("asd")

    assert result.status == Status.ERROR
    assert result.reason == "Unexpected response body"
