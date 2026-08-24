import json

from user_scanner.core import hudson


class DummyResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


class DummyClient:
    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc
        self.last_url = None
        self.last_params = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        self.last_url = url
        self.last_params = params
        if self._exc:
            raise self._exc
        return self._response


def make_client_factory(response=None, exc=None):
    instances = []

    def factory(*args, **kwargs):
        client = DummyClient(response=response, exc=exc)
        instances.append(client)
        return client

    factory.instances = instances
    return factory


def test_permission_skips_prompt_when_disabled(monkeypatch):
    monkeypatch.setattr(hudson, "load_config", lambda: {"auto_hudson_prompt": False})
    assert hudson.check_hudson_permission("bob") is True


def test_permission_yes(monkeypatch):
    monkeypatch.setattr(hudson, "load_config", lambda: {"auto_hudson_prompt": True})
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    assert hudson.check_hudson_permission("bob") is True


def test_permission_no(monkeypatch):
    monkeypatch.setattr(hudson, "load_config", lambda: {"auto_hudson_prompt": True})
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    assert hudson.check_hudson_permission("bob") is False


def test_permission_dont_ask_again_saves_preference(monkeypatch):
    monkeypatch.setattr(hudson, "load_config", lambda: {"auto_hudson_prompt": True})
    monkeypatch.setattr("builtins.input", lambda *_: "d")

    saved = {}
    monkeypatch.setattr(
        hudson, "update_hudson_preference", lambda v: saved.setdefault("value", v)
    )

    assert hudson.check_hudson_permission("bob") is True
    assert saved["value"] is False


def test_permission_reprompts_on_invalid_input(monkeypatch):
    monkeypatch.setattr(hudson, "load_config", lambda: {"auto_hudson_prompt": True})
    responses = iter(["bogus", "y"])
    monkeypatch.setattr("builtins.input", lambda *_: next(responses))
    assert hudson.check_hudson_permission("bob") is True


def test_update_hudson_preference_writes_config(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"auto_update_status": True, "auto_hudson_prompt": True}))

    monkeypatch.setattr(hudson, "_get_config_path", lambda: cfg_path)
    monkeypatch.setattr(hudson, "load_config", lambda: json.loads(cfg_path.read_text()))

    hudson.update_hudson_preference(False)

    saved = json.loads(cfg_path.read_text())
    assert saved["auto_hudson_prompt"] is False
    assert saved["auto_update_status"] is True


def test_run_hudson_scan_skips_without_permission(monkeypatch, capsys):
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: False)
    hudson.run_hudson_scan("bob")
    out = capsys.readouterr().out
    assert out == ""


def test_run_hudson_scan_reports_infections(monkeypatch, capsys):
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: True)
    data = {
        "stealers": [
            {
                "stealer_family": "RedLine",
                "date_compromised": "2024-01-01",
                "operating_system": "Windows 10",
                "computer_name": "DESKTOP-X",
                "antiviruses": ["Defender"],
                "top_logins": ["mail.example.com"],
            }
        ]
    }
    response = DummyResponse(200, data)
    monkeypatch.setattr(hudson.httpx, "Client", make_client_factory(response=response))

    hudson.run_hudson_scan("bob")
    out = capsys.readouterr().out
    assert "FOUND 1 INFOSTEALER" in out
    assert "RedLine" in out


def test_run_hudson_scan_no_infections(monkeypatch, capsys):
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: True)
    response = DummyResponse(200, {"stealers": []})
    monkeypatch.setattr(hudson.httpx, "Client", make_client_factory(response=response))

    hudson.run_hudson_scan("bob")
    out = capsys.readouterr().out
    assert "No infostealer infections found" in out


def test_run_hudson_scan_404(monkeypatch, capsys):
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: True)
    response = DummyResponse(404)
    monkeypatch.setattr(hudson.httpx, "Client", make_client_factory(response=response))

    hudson.run_hudson_scan("bob")
    out = capsys.readouterr().out
    assert "No data found" in out


def test_run_hudson_scan_unexpected_status(monkeypatch, capsys):
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: True)
    response = DummyResponse(500)
    monkeypatch.setattr(hudson.httpx, "Client", make_client_factory(response=response))

    hudson.run_hudson_scan("bob")
    out = capsys.readouterr().out
    assert "Hudson Rock API error: HTTP 500" in out


def test_run_hudson_scan_passes_target_via_params(monkeypatch, capsys):
    # Regression test: the target used to be interpolated directly into the
    # URL's query string (e.g. "...?email=user+tag@example.com"), which gets
    # silently mangled by any URL-decoding client/server (the '+' becomes a
    # space). It must be passed via `params` so httpx encodes it correctly.
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: True)
    response = DummyResponse(200, {"stealers": []})
    factory = make_client_factory(response=response)
    monkeypatch.setattr(hudson.httpx, "Client", factory)

    target = "user+tag@example.com"
    hudson.run_hudson_scan(target, is_email=True)

    client = factory.instances[-1]
    assert "?" not in client.last_url  # query string built via params, not the URL
    assert client.last_params == {"email": target}


def test_run_hudson_scan_handles_exception(monkeypatch, capsys):
    monkeypatch.setattr(hudson, "check_hudson_permission", lambda target: True)
    monkeypatch.setattr(
        hudson.httpx, "Client", make_client_factory(exc=RuntimeError("boom"))
    )

    hudson.run_hudson_scan("bob")
    out = capsys.readouterr().out
    assert "Error connecting to Hudson Rock" in out