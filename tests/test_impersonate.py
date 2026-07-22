from types import SimpleNamespace

from user_scanner.core import impersonate
from user_scanner.core.result import Result, Status


class FakeSession:
    instances = []

    def __init__(self, impersonate=None, proxies=None):
        self.impersonate = impersonate
        self.proxies = proxies
        self.calls = []
        FakeSession.instances.append(self)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def request(self, method, url, **kwargs):
        self.calls.append((url, kwargs))
        return SimpleNamespace(status_code=200, headers={}, text="ok")


def _reset(monkeypatch):
    impersonate._sessions.clear()
    impersonate._warmed.clear()
    FakeSession.instances.clear()
    monkeypatch.setattr(impersonate.cffi, "Session", FakeSession)
    monkeypatch.setattr(impersonate, "get_proxy", lambda: None)


def _process(response):
    return Result.taken() if response.status_code == 200 else Result.error("bad")


def test_warmup_runs_once_and_session_is_reused(monkeypatch):
    _reset(monkeypatch)

    r1 = impersonate.impersonate_validate(
        "https://site/a", _process, warmup_url="https://site/", show_url="SHOWN"
    )
    r2 = impersonate.impersonate_validate(
        "https://site/b", _process, warmup_url="https://site/"
    )

    assert r1.status == Status.TAKEN
    assert r1.url == "SHOWN"
    assert r2.status == Status.TAKEN

    assert len(FakeSession.instances) == 1
    session = FakeSession.instances[0]
    urls = [call[0] for call in session.calls]
    assert urls == ["https://site/", "https://site/a", "https://site/b"]

    profile_kwargs = session.calls[1][1]
    assert profile_kwargs.get("allow_redirects") is False
    assert profile_kwargs.get("timeout") == impersonate.DEFAULT_TIMEOUT


def test_request_reuses_warm_session(monkeypatch):
    _reset(monkeypatch)

    impersonate.impersonate_validate(
        "https://site/a", _process, warmup_url="https://site/"
    )
    resp = impersonate.impersonate_request(
        "https://site/graphql", method="POST", warmup_url="https://site/", json=[{"q": 1}]
    )

    assert resp.status_code == 200
    assert len(FakeSession.instances) == 1
    session = FakeSession.instances[0]
    urls = [call[0] for call in session.calls]
    # warm-up happens once, then the GET and the follow-up POST reuse it
    assert urls == ["https://site/", "https://site/a", "https://site/graphql"]


def test_exception_becomes_error_result(monkeypatch):
    _reset(monkeypatch)

    def boom(response):
        raise RuntimeError("kaboom")

    res = impersonate.impersonate_validate(
        "https://site/a", boom, warmup_url="https://site/", show_url="SHOWN"
    )

    assert res.status == Status.ERROR
    assert res.url == "SHOWN"
