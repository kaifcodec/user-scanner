import pytest

from user_scanner.utils import updater_logic


def test_skips_when_auto_update_disabled(monkeypatch):
    monkeypatch.setattr(updater_logic, "load_config", lambda: {"auto_update_status": False})

    def boom(url):
        raise AssertionError("should not check pypi when auto-update is disabled")

    monkeypatch.setattr(updater_logic, "get_pypi_version", boom)

    updater_logic.check_for_updates()  # should return silently


def test_no_prompt_when_up_to_date(monkeypatch, capsys):
    monkeypatch.setattr(updater_logic, "load_config", lambda: {"auto_update_status": True})
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: "1.2.3")
    monkeypatch.setattr(updater_logic, "load_local_version", lambda: ("1.2.3", None))

    updater_logic.check_for_updates()

    out = capsys.readouterr().out
    assert "New version available" not in out


def test_prompt_yes_triggers_update_and_exits(monkeypatch, capsys):
    monkeypatch.setattr(updater_logic, "load_config", lambda: {"auto_update_status": True})
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: "2.0.0")
    monkeypatch.setattr(updater_logic, "load_local_version", lambda: ("1.0.0", None))
    monkeypatch.setattr("builtins.input", lambda *_: "y")

    called = {}
    monkeypatch.setattr(updater_logic, "update_self", lambda: called.setdefault("update", True))

    with pytest.raises(SystemExit) as exc_info:
        updater_logic.check_for_updates()

    assert exc_info.value.code == 0
    assert called.get("update") is True


def test_prompt_dont_ask_again_saves_preference(monkeypatch, capsys):
    monkeypatch.setattr(updater_logic, "load_config", lambda: {"auto_update_status": True})
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: "2.0.0")
    monkeypatch.setattr(updater_logic, "load_local_version", lambda: ("1.0.0", None))
    monkeypatch.setattr("builtins.input", lambda *_: "d")

    saved = {}
    monkeypatch.setattr(
        updater_logic,
        "save_config_value",
        lambda key, value: saved.setdefault(key, value),
    )

    updater_logic.check_for_updates()  # should not raise SystemExit

    assert saved.get("auto_update_status") is False


def test_prompt_no_does_nothing(monkeypatch, capsys):
    monkeypatch.setattr(updater_logic, "load_config", lambda: {"auto_update_status": True})
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: "2.0.0")
    monkeypatch.setattr(updater_logic, "load_local_version", lambda: ("1.0.0", None))
    monkeypatch.setattr("builtins.input", lambda *_: "n")

    def boom():
        raise AssertionError("update_self should not be called")

    monkeypatch.setattr(updater_logic, "update_self", boom)

    updater_logic.check_for_updates()  # should not raise, not call update_self


def test_pypi_error_is_caught(monkeypatch, capsys):
    monkeypatch.setattr(updater_logic, "load_config", lambda: {"auto_update_status": True})

    def boom(url):
        raise RuntimeError("network down")

    monkeypatch.setattr(updater_logic, "get_pypi_version", boom)

    updater_logic.check_for_updates()  # should not raise

    out = capsys.readouterr().out
    assert "Update check failed" in out