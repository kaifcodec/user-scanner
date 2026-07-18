def test_set_concurrency():
    from user_scanner.core.email_orchestrator import set_concurrency
    import user_scanner.core.email_orchestrator as email_orchestrator
    
    original_max = email_orchestrator.MAX_CONCURRENT_REQUESTS
    set_concurrency(5)
    assert email_orchestrator.MAX_CONCURRENT_REQUESTS == 5
    
    # restore
    set_concurrency(original_max)
