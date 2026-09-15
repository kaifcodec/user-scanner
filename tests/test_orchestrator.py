import types
from types import SimpleNamespace

from user_scanner.core import orchestrator
from user_scanner.core.helpers import ScanConfig
from user_scanner.core.result import Result


def test_status_validate_available(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "make_request",
        lambda url, **kwargs: SimpleNamespace(status_code=200),
    )

    res = orchestrator.status_validate("http://example.com", available=200, taken=404)
    assert res.to_number() == 1  # AVAILABLE


def test_run_module_single_prints_json_and_csv(capsys):
    module = types.ModuleType("fake.testsite")
    module.__file__ = "<in-memory>/fake/testsite.py"

    def validate_testsite(username):
        return Result.available(username=username)

    setattr(module, "validate_testsite", validate_testsite)

    orchestrator.run_user_module(module, "bob", ScanConfig(show_all=True))
    out = capsys.readouterr().out
    assert "bob" in out  # Needs to be improved


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

    results = orchestrator.run_user_category(tmp_path, "someone", ScanConfig())
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].to_number() == 0  # TAKEN


def test_set_concurrency():
    from user_scanner.core.orchestrator import set_concurrency
    import user_scanner.core.orchestrator as orchestrator
    
    original_max = orchestrator.MAX_CONCURRENT_REQUESTS
    set_concurrency(10)
    assert orchestrator.MAX_CONCURRENT_REQUESTS == 10
    assert orchestrator._shared_executor._max_workers == max(10 * 2, 250)
    
    # restore
    set_concurrency(original_max)


def test_run_batch_multiple_categories_grouped(capsys, monkeypatch):
    mod1 = types.ModuleType("cat_a.site1")
    mod1.__file__ = "/path/to/user_scan/cat_a/site1.py"
    setattr(mod1, "validate_site1", lambda u: Result.taken(username=u))

    mod2 = types.ModuleType("cat_b.site2")
    mod2.__file__ = "/path/to/user_scan/cat_b/site2.py"
    setattr(mod2, "validate_site2", lambda u: Result.taken(username=u))

    mod3 = types.ModuleType("cat_a.site3")
    mod3.__file__ = "/path/to/user_scan/cat_a/site3.py"
    setattr(mod3, "validate_site3", lambda u: Result.taken(username=u))

    monkeypatch.setattr(orchestrator, "find_category", lambda m: m.__name__.split(".")[0].capitalize())
    monkeypatch.setattr(orchestrator, "get_site_name", lambda m: m.__name__.split(".")[-1].capitalize())

    results = orchestrator.run_user_module([mod1, mod2, mod3], "alice", ScanConfig(show_all=True))
    assert len(results) == 3

    out = capsys.readouterr().out
    assert "== CAT_A SITES ==" in out
    assert "== CAT_B SITES ==" in out

    cat_a_pos = out.find("== CAT_A SITES ==")
    cat_b_pos = out.find("== CAT_B SITES ==")
    assert cat_a_pos != -1 and cat_b_pos != -1
    assert cat_a_pos < cat_b_pos

    site1_pos = out.find("Site1")
    site2_pos = out.find("Site2")
    site3_pos = out.find("Site3")

    # Site1 and Site3 belong to Cat_a and must appear BEFORE Cat_b header
    assert cat_a_pos < site1_pos < cat_b_pos
    assert cat_a_pos < site3_pos < cat_b_pos
    # Site2 belongs to Cat_b and must appear AFTER Cat_b header
    assert site2_pos > cat_b_pos

