import sys
import threading
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from user_scanner.__main__ import main
from user_scanner.core import helpers
from user_scanner.core.result import Result
from user_scanner.core.helpers import _get_config_path, load_config, save_config_value, CONFIG_PATH


def test_get_site_name():
    def module(name: str) -> SimpleNamespace:
        return SimpleNamespace(**{"__name__": name})

    assert helpers.get_site_name(module("X")) == "X (Twitter)"
    assert helpers.get_site_name(module("x")) == "X (Twitter)"
    assert helpers.get_site_name(module("user_scanner.github")) == "Github"
    assert helpers.get_site_name(module("user_scanner.chess_com")) == "Chess.com"


@pytest.fixture
def run_main(monkeypatch):
    def _run(args):
        monkeypatch.setattr(sys, "argv", ["user-scanner"] + args)
        monkeypatch.setattr("user_scanner.__main__.check_for_updates", lambda: None)
        monkeypatch.setattr("user_scanner.__main__.update_self", lambda: None)
        monkeypatch.setattr("user_scanner.__main__.print_banner", lambda: None)
        # Added **kwargs to handle show_url argument
        monkeypatch.setattr(
            "user_scanner.__main__.run_email_module_batch",
            lambda m, t, config, **kwargs: [
                Result.taken(username=t, site_name=m, is_email=True)
            ],
        )
        # Added **kwargs to handle show_url argument
        monkeypatch.setattr(
            "user_scanner.__main__.run_user_module",
            lambda module, target, config, **kwargs: [
                Result.taken(username=target, site_name=module, is_email=False)
            ],
        )
        try:
            main()
            return 0
        except SystemExit as exc:
            return exc.code

    return _run


def test_bulk_emails_valid(tmp_path, run_main, capsys):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("""user1@example.com
    user2@test.com
    user3@domain.org""")

    exit_code = run_main(["-ef", str(email_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Loaded 3 emails" in out
    assert exit_code == 0


def test_bulk_emails_partially_valid(tmp_path, run_main, capsys):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("""user1@example.com
    invalid-email
    user3@domain.org""")

    exit_code = run_main(["-ef", str(email_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Skipping invalid email format: invalid-email" in out
    assert "Loaded 2 emails" in out
    assert exit_code == 0


def test_bulk_emails_single_valid(tmp_path, run_main, capsys):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("""user1@example.com
    invalid-email
    invalid-email3""")

    exit_code = run_main(["-ef", str(email_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Loaded 1 email" in out
    assert exit_code == 0


def test_bulk_emails_invalid(tmp_path, run_main):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("""invalid-email-1
    invalid-email-2
    invalid-email-3@""")

    exit_code = run_main(["-ef", str(email_file), "-m", "github"])
    assert exit_code == 1


def test_bulk_emails_empty_file(tmp_path, run_main):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("")
    exit_code = run_main(["-ef", str(email_file), "-m", "github"])
    assert exit_code == 1


def test_bulk_emails_no_file(run_main):
    exit_code = run_main(["-ef", "no_file.txt", "-m", "github"])
    assert exit_code == 1


def test_bulk_emails_skip_comments_blank_lines(tmp_path, run_main, capsys):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("""user1@example.com
    # comment

    user@example.com

    """)

    exit_code = run_main(["-ef", str(email_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Loaded 2 emails" in out
    assert exit_code == 0


def test_email_file_unreadable(tmp_path, run_main):
    email_file = tmp_path / "test_emails.txt"
    email_file.write_text("user@example.com")
    email_file.chmod(0)
    code = run_main(["-ef", str(email_file), "-m", "github"])
    assert code == 1


def test_bulk_usernames_valid(tmp_path, run_main, capsys):
    username_file = tmp_path / "test_usernames.txt"
    username_file.write_text("""user1
    user2
    user3""")

    exit_code = run_main(["-uf", str(username_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Loaded 3 usernames" in out
    assert exit_code == 0


def test_bulk_usernames_single_valid(tmp_path, run_main, capsys):
    username_file = tmp_path / "test_usernames.txt"
    username_file.write_text("user1")

    exit_code = run_main(["-uf", str(username_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Loaded 1 username" in out
    assert exit_code == 0


def test_bulk_usernames_empty_file(tmp_path, run_main):
    username_file = tmp_path / "test_usernames.txt"
    username_file.write_text("")
    exit_code = run_main(["-uf", str(username_file), "-m", "github"])
    assert exit_code == 1


def test_bulk_usernames_no_file(run_main):
    exit_code = run_main(["-uf", "no_file.txt", "-m", "github"])
    assert exit_code == 1


def test_bulk_usernames_skip_comments_blank_lines(tmp_path, run_main, capsys):
    username_file = tmp_path / "test_usernames.txt"
    username_file.write_text("""user1
# comment

    user2""")

    exit_code = run_main(["-uf", str(username_file), "-m", "github"])
    out = capsys.readouterr().out

    assert "Loaded 2 usernames" in out
    assert exit_code == 0


def test_username_file_unreadable(tmp_path, run_main):
    username_file = tmp_path / "test_usernames.txt"
    username_file.write_text("user")
    username_file.chmod(0)
    code = run_main(["-uf", str(username_file), "-m", "github"])
    assert code == 1


@patch("httpx.Client")
def test_validate_proxy_all_invalid(mock_client):
    instance = mock_client.return_value.__enter__.return_value
    response = MagicMock()
    response.status_code = 302
    instance.get.return_value = response

    proxies = ["http://proxy1.example.com:8080", "http://proxy2.example.com:3128"]
    result = helpers.validate_proxies(proxies)
    assert result == []


@patch("httpx.Client")
def test_validate_proxy_partially_invalid(mock_client):
    def side_effect(*args, **kwargs):
        proxy = kwargs.get("proxy")
        instance = MagicMock()
        if proxy and "invalid" in proxy:
            instance.get.side_effect = Exception("connection failed")
        else:
            response = MagicMock()
            response.status_code = 200
            instance.get.return_value = response
        instance.__enter__.return_value = instance
        instance.__exit__.return_value = None
        return instance

    mock_client.side_effect = side_effect
    proxies = ["http://invalid", "socks5://socks-proxy.example.com:1080"]
    result = helpers.validate_proxies(proxies)
    assert result == ["socks5://socks-proxy.example.com:1080"]


def test_validate_proxy_empty_list():
    result = helpers.validate_proxies([])
    assert result == []


@patch("httpx.Client")
def test_validate_proxy_timeout(mock_client):
    instance = mock_client.return_value.__enter__.return_value
    instance.get.side_effect = helpers.httpx.TimeoutException("timeout")
    proxies = ["http://proxy1.example.com:8080"]

    result = helpers.validate_proxies(proxies, timeout=1)
    assert result == []


@patch("httpx.Client")
def test_validate_proxy_single_worker(mock_client):
    instance = mock_client.return_value.__enter__.return_value
    response = MagicMock()
    response.status_code = 200
    instance.get.return_value = response

    proxies = ["http://proxy1.example.com:8080", "http://proxy2.example.com:3128"]
    result = helpers.validate_proxies(proxies, max_workers=1)

    assert result == proxies


def test_proxy_manager_add_protocol(tmp_path):
    proxy_file = tmp_path / "test_proxies.txt"
    proxy_file.write_text("""proxy1.example.com:8080
socks5://socks-proxy.example.com:1080""")

    manager = helpers.ProxyManager(str(proxy_file))

    assert manager.count() == 2
    assert manager.proxies[0].startswith("http://")
    assert manager.proxies[1].startswith("socks5://")


def test_proxy_manager_preserves_explicit_schemes(tmp_path):
    proxy_file = tmp_path / "test_proxies.txt"
    proxy_file.write_text("""socks4://legacy-proxy.example.com:1080
socks5h://onion-proxy.example.com:9050
https://secure-proxy.example.com:443""")

    manager = helpers.ProxyManager(str(proxy_file))

    assert manager.proxies == [
        "socks4://legacy-proxy.example.com:1080",
        "socks5h://onion-proxy.example.com:9050",
        "https://secure-proxy.example.com:443",
    ]


def test_proxy_manager_no_poxy_file(tmp_path):
    with pytest.raises(FileNotFoundError) as exc_info:
        helpers.ProxyManager("no_proxy_file.txt")
    assert exc_info.type is FileNotFoundError


def test_proxy_manager_empty_file_only_comments(tmp_path):
    proxy_file = tmp_path / "test_proxy.txt"
    proxy_file.write_text("""#comment

    """)
    with pytest.raises(Exception):
        helpers.ProxyManager(str(proxy_file))


def test_proxy_rotation(tmp_path):
    proxy_file = tmp_path / "test_proxy.txt"
    proxy_file.write_text("""http://1
http://2
http://3""")
    manager = helpers.ProxyManager(str(proxy_file))

    assert manager.get_next_proxy() == "http://1"
    assert manager.get_next_proxy() == "http://2"
    assert manager.get_next_proxy() == "http://3"
    assert manager.get_next_proxy() == "http://1"


def test_single_proxy_rotation(tmp_path):
    proxy_file = tmp_path / "test_proxy.txt"
    proxy_file.write_text("http://1")
    manager = helpers.ProxyManager(str(proxy_file))
    for _ in range(3):
        assert manager.get_next_proxy() == "http://1"


def test_global_manager(tmp_path):
    proxy_file = tmp_path / "test_proxy.txt"
    proxy_file.write_text("""http://1
http://2""")

    helpers.set_proxy_manager(str(proxy_file))

    p1 = helpers.get_proxy()
    p2 = helpers.get_proxy()

    assert p1 != p2
    assert helpers.get_proxy_count() == 2


def test_thread_safe_rotation(tmp_path):
    proxy_file = tmp_path / "test_proxy.txt"
    proxy_file.write_text("""http://1
http://2
http://3""")
    manager = helpers.ProxyManager(str(proxy_file))
    results = []

    def worker():
        results.append(manager.get_next_proxy())

    threads = [threading.Thread(target=worker) for _ in range(50)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 50


def test_get_config_path_default(monkeypatch):
    monkeypatch.delenv("USER_SCANNER_CONFIG", raising=False)
    path = _get_config_path()
    assert path == CONFIG_PATH

def test_get_config_path_env_override(monkeypatch, tmp_path):
    custom_path = tmp_path / "custom_config.json"
    monkeypatch.setenv("USER_SCANNER_CONFIG", str(custom_path))
    path = _get_config_path()
    assert path == custom_path

def test_load_config_creates_default(tmp_path):
    config_file = tmp_path / "new_config.json"
    data = load_config(path=config_file)

    assert config_file.exists()
    assert data["auto_update_status"] is True
    assert data["auto_hudson_prompt"] is True

def test_load_config_reads_existing(tmp_path):
    config_file = tmp_path / "existing.json"
    existing_data = {
        "auto_update_status": False,
        "auto_hudson_prompt": False
    }
    config_file.write_text(json.dumps(existing_data))

    data = load_config(path=config_file)
    assert data == existing_data

def test_save_config_value_updates_keys(tmp_path):
    config_file = tmp_path / "test_save.json"

    save_config_value("auto_update_status", False, path=config_file)
    data = load_config(path=config_file)
    assert data["auto_update_status"] is False
    assert data["auto_hudson_prompt"] is True

    save_config_value("auto_hudson_prompt", False, path=config_file)
    data = load_config(path=config_file)
    assert data["auto_hudson_prompt"] is False
    assert data["auto_update_status"] is False

def test_load_config_handles_corrupt_json(tmp_path):
    config_file = tmp_path / "corrupt.json"
    config_file.write_text("{ 'broken': true, }")

    data = load_config(path=config_file)
    assert data["auto_update_status"] is True
    assert data["auto_hudson_prompt"] is True

def test_save_config_value_creates_directory(tmp_path):
    nested_path = tmp_path / "subdir" / "nested_config.json"

    save_config_value("auto_update_status", True, path=nested_path)

    assert nested_path.exists()
    assert nested_path.parent.is_dir()

def test_hudson_config_value():
    from user_scanner.core.helpers import _get_config_path, load_config

    actual_path = _get_config_path()
    data = load_config(path=actual_path)
    status = data.get("auto_hudson_prompt")

    assert status is True, f"FAIL: Actual config at {actual_path} has auto_hudson_prompt set to {status} (Expected: True)"
