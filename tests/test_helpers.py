import sys
import pytest
from user_scanner.core import helpers
from user_scanner.__main__ import main
from user_scanner.core.result import Result
from types import SimpleNamespace

def test_generate_permutations():
    perms = helpers.generate_permutations("user", "ab", limit=None)    
    assert "user" in perms  
    # All permutations must be valid
    assert all(
        p == "user" or
        (p.startswith("user") and len(p) > len("user"))
        for p in perms
    )
    
    assert len(perms) > 1

def test_generate_permutations_email():
    perms = helpers.generate_permutations("john@email.com", "abc", limit=None, is_email=True)    
    assert "john@email.com" in perms  
    assert all(
        p == "john@email.com" or
        (p.startswith("john") and len(p) > len("john@email.com") and p.endswith("@email.com"))
        for p in perms
    )
    assert len(perms) > 1

def test_get_site_name():
    def module(name:str) -> SimpleNamespace:
        return SimpleNamespace(**{"__name__":name})
    assert helpers.get_site_name(module("X")) == "X (Twitter)"
    assert helpers.get_site_name(module("x")) == "X (Twitter)"
    assert helpers.get_site_name(module("user_scanner.github")) == "Github"
    assert helpers.get_site_name(module("user_scanner.chess_com")) == "Chess.com"

@pytest.fixture
def run_main(monkeypatch):
    def _run(args):
        monkeypatch.setattr(sys, "argv", ["user-scanner"] + args)
        monkeypatch.setattr("user_scanner.utils.updater_logic.check_for_updates", lambda: None)
        monkeypatch.setattr("user_scanner.utils.update.update_self", lambda: None)
        monkeypatch.setattr(
            "user_scanner.core.email_orchestrator.run_email_module_batch",
            lambda m, t: [Result.taken(username=t, site_name=m, is_email=True)])
        monkeypatch.setattr(
        "user_scanner.core.orchestrator.run_user_module",
        lambda module, target: [Result.taken(username=target, site_name=module, is_email=False)]
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

    assert "Loaded 1 emails" in out
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





    

