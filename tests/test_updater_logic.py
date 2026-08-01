from user_scanner.utils import updater_logic


def test_skips_prompt_when_pypi_unreachable(monkeypatch, capsys):
    monkeypatch.setattr(
        updater_logic, "load_config", lambda: {"auto_update_status": True}
    )
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: None)
    monkeypatch.setattr(
        updater_logic, "load_local_version", lambda: ("1.4.1.9", "local")
    )

    called = []
    monkeypatch.setattr("builtins.input", lambda *_: called.append(True))

    updater_logic.check_for_updates()

    out = capsys.readouterr().out
    assert "New version available" not in out
    assert "Could not reach PyPI" in out
    assert called == []  # input() never invoked


def test_prompts_when_real_update_available(monkeypatch, capsys):
    monkeypatch.setattr(
        updater_logic, "load_config", lambda: {"auto_update_status": True}
    )
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: "9.9.9")
    monkeypatch.setattr(
        updater_logic, "load_local_version", lambda: ("1.4.1.9", "local")
    )
    monkeypatch.setattr("builtins.input", lambda _: "n")

    updater_logic.check_for_updates()

    out = capsys.readouterr().out
    assert "New version available" in out


def test_no_prompt_when_up_to_date(monkeypatch, capsys):
    monkeypatch.setattr(
        updater_logic, "load_config", lambda: {"auto_update_status": True}
    )
    monkeypatch.setattr(updater_logic, "get_pypi_version", lambda url: "1.4.1.9")
    monkeypatch.setattr(
        updater_logic, "load_local_version", lambda: ("1.4.1.9", "local")
    )

    called = []
    monkeypatch.setattr("builtins.input", lambda *_: called.append(True))

    updater_logic.check_for_updates()

    out = capsys.readouterr().out
    assert "New version available" not in out
    assert called == []