from types import SimpleNamespace

from user_scanner.core.result import Status
from user_scanner.user_scan.gaming import stackb


def _profile_html(username="777h"):
    return f"""
    <html>
      <head>
        <link rel="canonical" href="https://stackb.net/@{username}">
        <meta property="og:type" content="profile">
        <meta property="og:title" content="μ (@{username}) — Stack B">
        <meta property="og:description" content="Bio text. Ранг: Gold2. Подписчики: 1191. Профиль на Stack B">
        <meta property="og:url" content="https://stackb.net/@{username}">
        <meta property="og:image" content="https://cdn-msk.stackb.net/avatar.png">
        <script type="application/ld+json">{{
          "@context": "https://schema.org",
          "@type": "ProfilePage",
          "name": "μ (@{username}) — Stack B",
          "url": "https://stackb.net/@{username}",
          "mainEntity": {{
            "@type": "Person",
            "name": "μ",
            "url": "https://stackb.net/@{username}",
            "image": "https://cdn-msk.stackb.net/avatar.png",
            "description": "Bio text",
            "identifier": "@{username}"
          }}
        }}</script>
      </head>
      <body>
        <div wire:snapshot="{{&quot;memo&quot;:{{&quot;name&quot;:&quot;profile&quot;}}}}">
          <a href="https://stackb.net/@{username}/followers">1191 Подписчиков</a>
        </div>
      </body>
    </html>
    """


def _mock_generic_validate(monkeypatch, response_text, status_code=200):
    def fake_generic_validate(url, process, **kwargs):
        response = SimpleNamespace(status_code=status_code, text=response_text)
        return process(response).update(url=kwargs.get("show_url"))

    monkeypatch.setattr(stackb, "generic_validate", fake_generic_validate)


def test_stackb_taken(monkeypatch):
    _mock_generic_validate(monkeypatch, _profile_html())

    result = stackb.validate_stackb("777h")

    assert result.status == Status.TAKEN
    assert result.url == "https://stackb.net/@777h"
    assert result.extra["display_name"] == "μ"
    assert result.extra["bio"] == "Bio text"
    assert result.extra["avatar"] == "https://cdn-msk.stackb.net/avatar.png"
    assert result.extra["followers"] == 1191
    assert result.extra["rank"] == "Gold2"
    assert result.extra["profile_url"] == "https://stackb.net/@777h"


def test_stackb_strips_leading_at(monkeypatch):
    _mock_generic_validate(monkeypatch, _profile_html())

    result = stackb.validate_stackb("@777h")

    assert result.status == Status.TAKEN
    assert result.url == "https://stackb.net/@777h"


def test_stackb_available(monkeypatch):
    body = "<html><body><p>404</p><h1>Страница не найдена</h1></body></html>"
    _mock_generic_validate(monkeypatch, body, status_code=404)

    result = stackb.validate_stackb("missing-user")

    assert result.status == Status.AVAILABLE


def test_stackb_rejects_path_separator_before_request(monkeypatch):
    def fail_generic_validate(*args, **kwargs):
        raise AssertionError("generic_validate should not be called")

    monkeypatch.setattr(stackb, "generic_validate", fail_generic_validate)

    result = stackb.validate_stackb("bad/user")

    assert result.status == Status.ERROR
    assert result.reason == "Username contains unsafe URL path characters"


def test_stackb_allows_internal_special_character(monkeypatch):
    _mock_generic_validate(monkeypatch, _profile_html("bad@user"))

    result = stackb.validate_stackb("bad@user")

    assert result.status == Status.TAKEN
    assert result.url == "https://stackb.net/@bad%40user"
    assert result.extra["profile_url"] == "https://stackb.net/@bad@user"


def test_stackb_ambiguous_page_errors(monkeypatch):
    body = """
    <html>
      <head>
        <link rel="canonical" href="https://stackb.net/@777h">
        <meta property="og:type" content="website">
      </head>
    </html>
    """
    _mock_generic_validate(monkeypatch, body)

    result = stackb.validate_stackb("777h")

    assert result.status == Status.ERROR
    assert result.reason == "Unexpected response body"
