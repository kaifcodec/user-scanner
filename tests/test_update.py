from user_scanner.utils.updater_logic import load_config, save_config_change


def test_config_json():
    configs = load_config()
    assert "auto_update_status" in configs
    # Shouldn't allow PR with this configuration set to False
    # Need to be carefull if another test sets it to False
    assert configs["auto_update_status"] == True


def test_config_set():
    def get_status(): return load_config()["auto_update_status"]
    save_config_change(False)
    assert get_status() == False
    save_config_change(True)
    assert get_status() == True
