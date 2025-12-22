import json
from types import SimpleNamespace
from user_scanner.core import version


def test_load_local_version(tmp_path, monkeypatch):
    vf = tmp_path / "version.json"
    vf.write_text(json.dumps({"version": "9.9.9", "version_type": "local"}))
    monkeypatch.setattr(version, "VERSION_FILE", vf)
    ver, typ = version.load_local_version()
    assert ver == "9.9.9"
    assert typ == "local"


def test_get_pypi_version(monkeypatch):
    # Mock httpx.get to return an object with .json()
    monkeypatch.setattr(version.httpx, "get",
                        lambda url, timeout=7: SimpleNamespace(json=lambda: {"info": {"version": "1.2.3"}}))
    pv = version.get_pypi_version("http://fake")
    assert pv == "1.2.3"
