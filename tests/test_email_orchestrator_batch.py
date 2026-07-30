import types

from user_scanner.core import email_orchestrator
from user_scanner.core.helpers import ScanConfig
from user_scanner.core.result import Result


def _make_module(name, func=None):
    module = types.ModuleType(name)
    module.__file__ = f"<in-memory>/{name}.py"
    if func is not None:
        setattr(module, f"validate_{name.split('.')[-1]}", func)
    return module


def test_run_email_module_batch_returns_result():
    def validate_testsite(email):
        return Result.taken(username=email)

    module = _make_module("testsite", validate_testsite)

    results = email_orchestrator.run_email_module_batch(
        module, "bob@example.com", ScanConfig()
    )

    assert len(results) == 1
    assert results[0].to_number() == 0  # TAKEN
    assert results[0].is_email is True


def test_run_email_module_batch_missing_validate_func():
    module = types.ModuleType("testsite")
    module.__file__ = "<in-memory>/testsite.py"

    results = email_orchestrator.run_email_module_batch(
        module, "bob@example.com", ScanConfig()
    )

    assert len(results) == 1
    assert results[0].to_number() == 2  # ERROR
    assert "has no validate_ function" in results[0].get_reason()


def test_async_worker_skips_loud_when_not_allowed(monkeypatch):
    def validate_testsite(email):
        return Result.taken(username=email)

    module = _make_module("testsite", validate_testsite)

    monkeypatch.setattr(email_orchestrator, "is_loud", lambda site_name, is_email=False: True)

    results = email_orchestrator.run_email_module_batch(
        module, "bob@example.com", ScanConfig(allow_loud=False)
    )

    assert len(results) == 1
    assert results[0].to_number() == 3  # SKIPPED


def test_run_email_category_batch(monkeypatch, tmp_path):
    def validate(email):
        return Result.available(username=email)

    module = _make_module("testsite", validate)

    monkeypatch.setattr(email_orchestrator, "load_modules", lambda p: [module])

    results = email_orchestrator.run_email_category_batch(
        tmp_path, "bob@example.com", ScanConfig()
    )

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].to_number() == 1  # AVAILABLE


def test_run_email_full_batch(monkeypatch):
    def validate(email):
        return Result.taken(username=email)

    module = _make_module("testsite", validate)

    monkeypatch.setattr(
        email_orchestrator, "load_categories", lambda *a, **k: {"dev": "fake_path"}
    )
    monkeypatch.setattr(email_orchestrator, "load_modules", lambda p: [module])

    results = email_orchestrator.run_email_full_batch("bob@example.com", ScanConfig())

    assert len(results) == 1
    assert results[0].to_number() == 0  # TAKEN