def test_set_concurrency():
    from user_scanner.core.email_orchestrator import set_concurrency
    import user_scanner.core.email_orchestrator as email_orchestrator
    
    original_max = email_orchestrator.MAX_CONCURRENT_REQUESTS
    set_concurrency(5)
    assert email_orchestrator.MAX_CONCURRENT_REQUESTS == 5
    
    # restore
    set_concurrency(original_max)


def test_run_email_batch_multiple_categories_grouped(capsys, monkeypatch):
    import types
    from user_scanner.core import email_orchestrator
    from user_scanner.core.helpers import ScanConfig
    from user_scanner.core.result import Result

    mod1 = types.ModuleType("cat_a.site1")
    mod1.__file__ = "/path/to/email_scan/cat_a/site1.py"

    async def val1(e):
        return Result.taken(username=e)

    setattr(mod1, "validate_site1", val1)

    mod2 = types.ModuleType("cat_b.site2")
    mod2.__file__ = "/path/to/email_scan/cat_b/site2.py"

    async def val2(e):
        return Result.taken(username=e)

    setattr(mod2, "validate_site2", val2)

    mod3 = types.ModuleType("cat_a.site3")
    mod3.__file__ = "/path/to/email_scan/cat_a/site3.py"

    async def val3(e):
        return Result.taken(username=e)

    setattr(mod3, "validate_site3", val3)

    monkeypatch.setattr(email_orchestrator, "find_category", lambda m: m.__name__.split(".")[0].capitalize())
    monkeypatch.setattr(email_orchestrator, "get_site_name", lambda m: m.__name__.split(".")[-1].capitalize())

    results = email_orchestrator.run_email_module_batch([mod1, mod2, mod3], "alice@example.com", ScanConfig(show_all=True))
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

