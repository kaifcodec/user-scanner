import types
from types import SimpleNamespace
from user_scanner.core import orchestrator
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

def test_generate_permutations_email():
    perms = orchestrator.generate_permutations("john@email.com", "abc", limit=None, is_email=True)    
    assert "john@email.com" in perms  
    assert all(
        p == "john@email.com" or
        (p.startswith("john") and len(p) > len("john@email.com") and p.endswith("@email.com"))
        for p in perms
    )
    assert len(perms) > 1

def test_run_module_single_prints_json_and_csv(capsys):
    module = types.ModuleType("fake.testsite")
    module.__file__ = "<in-memory>/fake/testsite.py"

    def validate_testsite(username):
        return Result.available(username=username)

    setattr(module, "validate_testsite", validate_testsite)

    orchestrator.run_user_module(module, "bob")
    out = capsys.readouterr().out
    assert 'bob' in out #Needs to be improved



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

    results = orchestrator.run_user_category(tmp_path, "someone")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].to_number() == 0  # TAKEN
