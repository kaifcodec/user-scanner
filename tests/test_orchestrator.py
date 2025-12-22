import types
from types import SimpleNamespace
from user_scanner.core import orchestrator
from user_scanner.cli.printer import Printer
from user_scanner.core.result import Result


def test_status_validate_available(monkeypatch):
    monkeypatch.setattr(orchestrator, "make_request",
                        lambda url, **kwargs: SimpleNamespace(status_code=200))

    res = orchestrator.status_validate("http://example.com", available=200, taken=404)
    assert res.to_number() == 1  # AVAILABLE


def test_generate_permutations():
    perms = orchestrator.generate_permutations("user", "ab", limit=None)    
    assert "user" in perms  
    # All permutations must be valid
    assert all(
        p == "user" or
        (p.startswith("user") and len(p) > len("user"))
        for p in perms
    )
    
    assert len(perms) > 1

def test_run_module_single_prints_json_and_csv(capsys):
    module = types.ModuleType("fake.testsite")
    module.__file__ = "<in-memory>/fake/testsite.py"

    def validate_testsite(username):
        return Result.available(username=username)

    setattr(module, "validate_testsite", validate_testsite)

    p_json = Printer("json")
    orchestrator.run_module_single(module, "bob", p_json, last=True)
    out = capsys.readouterr().out
    assert '"username": "bob"' in out

    p_csv = Printer("csv")
    orchestrator.run_module_single(module, "bob", p_csv, last=True)
    out2 = capsys.readouterr().out
    assert "bob" in out2
    assert "Testsite" in out2 or "testsite" in out2


def test_run_checks_category_threaded(monkeypatch, tmp_path):
    # Create a temporary module file to simulate a real module file
    module = types.ModuleType("fake.testsite")
    module.__file__ = str(tmp_path / "category" / "testsite.py")

    def validate(username):
        return Result.taken(username=username)

    setattr(module, "validate_testsite", validate)

    # Patch load_modules to return our single module
    monkeypatch.setattr(orchestrator, "load_modules", lambda p: [module])
    monkeypatch.setattr(orchestrator, "get_site_name", lambda m: "Testsite")

    p = Printer("console")
    results = orchestrator.run_checks_category(tmp_path, "someone", p, last=True)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].to_number() == 0  # TAKEN
