from user_scanner.core import helpers as hl


def test_default_config():
    configs = hl.load_config()
    assert "auto_update_status" in configs
    # Make sure config.json has "auto_update_status" set to true
    assert configs["auto_update_status"]


def test_config_json(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setenv("USER_SCANNER_CONFIG", str(cfg))
    configs = hl.load_config()
    assert "auto_update_status" in configs
    # Should be default True
    assert configs["auto_update_status"] is True


def test_config_set(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setenv("USER_SCANNER_CONFIG", str(cfg))

    def get_status():
        return hl.load_config()["auto_update_status"]

    hl.save_config_value("auto_update_status", False)
    assert get_status() is False

    hl.save_config_value("auto_update_status", True)
    assert get_status() is True
