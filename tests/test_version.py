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

def test_load_local_version_file_missing(tmp_path, monkeypatch):
    vf = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(version, "VERSION_FILE", vf)
    ver, typ = version.load_local_version()
    assert ver == "N/A"
    assert typ == "file_missing"


def test_load_local_version_corrupted_json(tmp_path, monkeypatch):
    vf = tmp_path / "version.json"
    vf.write_text("{not valid json")
    monkeypatch.setattr(version, "VERSION_FILE", vf)
    ver, typ = version.load_local_version()
    assert ver == "N/A"
    assert typ == "json_error"


def test_load_local_version_generic_error(tmp_path, monkeypatch):
    # A directory instead of a file triggers a generic (non-FileNotFound,
    # non-JSONDecodeError) exception when read_text() is called on it.
    vf = tmp_path / "version_dir"
    vf.mkdir()
    monkeypatch.setattr(version, "VERSION_FILE", vf)
    ver, typ = version.load_local_version()
    assert ver == "N/A"
    assert typ == "error"


def test_load_local_version_missing_keys_defaults(tmp_path, monkeypatch):
    vf = tmp_path / "version.json"
    vf.write_text(json.dumps({}))  # no "version" or "version_type" keys
    monkeypatch.setattr(version, "VERSION_FILE", vf)
    ver, typ = version.load_local_version()
    assert ver == "error_report_via_gh_issues"
    assert typ == "local"


def test_get_pypi_version_returns_none_on_error(monkeypatch, capsys):
    def boom(url, timeout=7):
        raise RuntimeError("network down")

    monkeypatch.setattr(version.httpx, "get", boom)
    pv = version.get_pypi_version("http://fake")
    assert pv is None
