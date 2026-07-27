from user_scanner.core import loud_prompt
from user_scanner.core.helpers import _get_config_path, load_config, save_config_value


def test_loud_module_config_value():
    actual_path = _get_config_path()
    data = load_config(path=actual_path)
    status = data.get("auto_loud_single_module_prompt")
    assert status is True, f"FAIL: Actual config at {actual_path} has auto_loud_single_module_prompt set to {status} (Expected: True)"


def test_check_loud_module_permission_tty_yes(monkeypatch):
    monkeypatch.setattr(loud_prompt.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "y")
    monkeypatch.setattr(loud_prompt, "load_config", lambda: {"auto_loud_single_module_prompt": True})
    assert loud_prompt.check_loud_module_permission("Netflix", "test@example.com") is True


def test_check_loud_module_permission_tty_no(monkeypatch):
    monkeypatch.setattr(loud_prompt.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setattr(loud_prompt, "load_config", lambda: {"auto_loud_single_module_prompt": True})
    assert loud_prompt.check_loud_module_permission("Netflix", "test@example.com") is False


def test_check_loud_module_permission_tty_dont_ask(monkeypatch):
    saved = {}
    monkeypatch.setattr(loud_prompt.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "d")
    monkeypatch.setattr(loud_prompt, "load_config", lambda: {"auto_loud_single_module_prompt": True})
    monkeypatch.setattr(loud_prompt, "update_loud_module_preference", lambda v: saved.setdefault("value", v))
    assert loud_prompt.check_loud_module_permission("Netflix", "test@example.com") is True
    assert saved["value"] is False


def test_check_loud_module_permission_no_tty(monkeypatch):
    monkeypatch.setattr(loud_prompt.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(loud_prompt, "load_config", lambda: {"auto_loud_single_module_prompt": True})
    called = []
    monkeypatch.setattr("builtins.input", lambda *_: called.append(True))
    assert loud_prompt.check_loud_module_permission("Netflix", "test@example.com") is False
    assert called == []  # input() never invoked


def test_check_loud_module_permission_saved_preference(monkeypatch):
    monkeypatch.setattr(loud_prompt, "load_config", lambda: {"auto_loud_single_module_prompt": False})
    called = []
    monkeypatch.setattr("builtins.input", lambda *_: called.append(True))
    assert loud_prompt.check_loud_module_permission("Netflix", "test@example.com") is True
    assert called == []

def test_save_config_value_preserves_loud_module_key(tmp_path):
    config_file = tmp_path / "test_save.json"

    # Updating an unrelated key must not disturb auto_loud_single_module_prompt
    save_config_value("auto_update_status", False, path=config_file)
    data = load_config(path=config_file)
    assert data["auto_loud_single_module_prompt"] is True

    # Explicitly flipping it should persist correctly and not affect others
    save_config_value("auto_loud_single_module_prompt", False, path=config_file)
    data = load_config(path=config_file)
    assert data["auto_loud_single_module_prompt"] is False
    assert data["auto_update_status"] is False