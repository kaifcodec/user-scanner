from user_scanner.utils import updater_logic as ul

def test_default_config():
    configs = ul.load_config()
    assert "auto_update_status" in configs
    # Make sure config.json has "auto_update_status" set to true
    assert configs["auto_update_status"]

def test_config_json(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setenv("USER_SCANNER_CONFIG", str(cfg))
    configs = ul.load_config()
    assert "auto_update_status" in configs
    # Should be default True
    assert configs["auto_update_status"] is True


def test_config_set(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setenv("USER_SCANNER_CONFIG", str(cfg))

    def get_status():
        return ul.load_config()["auto_update_status"]

    ul.save_config_change(False)
    assert get_status() is False

    ul.save_config_change(True)
    assert get_status() is True
