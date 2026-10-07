import pytest
from unittest.mock import patch

from user_scanner.mcp.handlers import call_tool, execute_scan
from user_scanner.core.helpers import ScanConfig
from user_scanner.core.result import Result


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
async def test_call_tool_unknown():
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("nonexistent_tool", {})


@pytest.mark.anyio
async def test_execute_scan_missing_target():
    with pytest.raises(ValueError, match="Missing 'username' argument"):
        await execute_scan({"category": "social"}, is_email=False)
        
    with pytest.raises(ValueError, match="Missing 'email' argument"):
        await execute_scan({"category": "social"}, is_email=True)


@pytest.mark.anyio
async def test_execute_scan_category_and_module_together():
    with pytest.raises(ValueError, match="Cannot specify both 'category' and 'module'"):
        await execute_scan(
            {"username": "testuser", "category": "social", "module": "github"},
            is_email=False,
        )


@pytest.mark.anyio
@patch("user_scanner.mcp.handlers._run_scan")
@patch("user_scanner.mcp.handlers.set_global_timeout")
@patch("user_scanner.mcp.handlers.set_proxy_manager")
@patch("user_scanner.mcp.handlers.set_user_concurrency")
@patch("user_scanner.mcp.handlers.set_email_concurrency")
async def test_execute_scan_argument_mapping(
    mock_set_email_conc,
    mock_set_user_conc,
    mock_set_proxy,
    mock_set_timeout,
    mock_run_scan,
):
    mock_run_scan.return_value = [Result.available()]
    
    arguments = {
        "username": "testuser",
        "allow_loud": True,
        "no_nsfw": True,
        "timeout": 15,
        "concurrency": 10,
        "proxies": ["http://127.0.0.1:8080"],
    }
    
    await execute_scan(arguments, is_email=False)
    
    # Assert proxies were set
    mock_set_proxy.assert_any_call(proxies=["http://127.0.0.1:8080"])
    
    # Assert timeout was set
    mock_set_timeout.assert_any_call(15.0)
    
    # Assert concurrency was set
    mock_set_user_conc.assert_any_call(10)
    mock_set_email_conc.assert_any_call(10)
    
    # Assert run_scan received correct ScanConfig
    # signature: _run_scan(target, config, is_email, category, module_name)
    call_args = mock_run_scan.call_args[0]
    config = call_args[1]
    
    assert isinstance(config, ScanConfig)
    assert config.allow_loud is True
    assert config.no_nsfw is True
    assert config.timeout == 15.0


@pytest.mark.anyio
@patch("user_scanner.mcp.handlers._run_scan")
async def test_execute_scan_module_normalization(mock_run_scan):
    mock_run_scan.return_value = [Result.available()]
    
    # Passing a module name with a dot (e.g. from the list_available_modules output)
    arguments = {
        "username": "testuser",
        "module": "Made.porn", 
    }
    
    await execute_scan(arguments, is_email=False)
    
    call_args = mock_run_scan.call_args[0]
    module_name = call_args[4]
    
    # It should normalize to an underscore
    assert module_name == "Made_porn"


@pytest.mark.anyio
@patch("user_scanner.mcp.handlers.run_cross_scan")
@patch("user_scanner.mcp.handlers._run_scan")
async def test_execute_scan_cross_scan_runs_off_event_loop(mock_run_scan, mock_cross_scan):
    """run_cross_scan uses asyncio.run() internally, so it must not run on the event loop thread."""
    import asyncio
    import threading

    loop_thread = threading.get_ident()
    seen = {}

    def fake_cross_scan(results, configs, cross_configs):
        seen["thread"] = threading.get_ident()
        # Mirrors the orchestrators, which call asyncio.run() internally.
        asyncio.run(asyncio.sleep(0))
        return [Result.taken()]

    mock_run_scan.return_value = [Result.available()]
    mock_cross_scan.side_effect = fake_cross_scan

    await execute_scan({"username": "testuser", "cross_scan": True}, is_email=False)

    assert seen["thread"] != loop_thread


@pytest.mark.anyio
async def test_cancelling_mcp_scan_defers_cleanup_until_worker_terminates(monkeypatch):
    import asyncio
    import sys
    import threading
    from user_scanner.core import helpers
    from user_scanner.mcp import handlers

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    observations = {}
    original_stdout = sys.stdout

    def worker(*args):
        observations["initial_proxy"] = helpers.get_proxy()
        started.set()
        try:
            assert release.wait(5)
            observations["late_proxy"] = helpers.get_proxy()
            observations["stdout_restored"] = sys.stdout is original_stdout
            return []
        finally:
            finished.set()

    monkeypatch.setattr(handlers, "_run_scan", worker)

    handlers._scan_lock = asyncio.Lock()
    task = asyncio.create_task(
        handlers.execute_scan(
            {"username": "audit", "proxies": ["http://127.0.0.1:12345"]},
            is_email=False,
        )
    )

    assert await asyncio.to_thread(started.wait, 5)
    task.cancel()

    await asyncio.sleep(0.05)
    assert not finished.is_set(), "Worker should still be alive"
    assert handlers._scan_lock.locked(), "Lock must remain held while worker is alive"
    assert helpers.get_proxy() == "http://127.0.0.1:12345", "Proxy must not be cleared while worker is alive"

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert finished.is_set()
    assert not handlers._scan_lock.locked()
    assert helpers.get_proxy() is None
    assert observations == {
        "initial_proxy": "http://127.0.0.1:12345",
        "late_proxy": "http://127.0.0.1:12345",
        "stdout_restored": False,
    }


@pytest.mark.anyio
async def test_cancelling_mcp_cross_scan_defers_cleanup(monkeypatch):
    import asyncio
    import sys
    import threading
    from user_scanner.core import helpers
    from user_scanner.mcp import handlers

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    observations = {}
    original_stdout = sys.stdout

    def fake_run_scan(*args):
        return [Result.taken()]

    def fake_cross_scan(*args):
        observations["initial_proxy"] = helpers.get_proxy()
        started.set()
        try:
            assert release.wait(5)
            observations["late_proxy"] = helpers.get_proxy()
            observations["stdout_restored"] = sys.stdout is original_stdout
            return []
        finally:
            finished.set()

    monkeypatch.setattr(handlers, "_run_scan", fake_run_scan)
    monkeypatch.setattr(handlers, "run_cross_scan", fake_cross_scan)

    handlers._scan_lock = asyncio.Lock()
    task = asyncio.create_task(
        handlers.execute_scan(
            {
                "username": "audit",
                "cross_scan": True,
                "proxies": ["http://127.0.0.1:12345"],
            },
            is_email=False,
        )
    )

    assert await asyncio.to_thread(started.wait, 5)
    task.cancel()

    await asyncio.sleep(0.05)
    assert not finished.is_set(), "Cross-scan worker should still be alive"
    assert handlers._scan_lock.locked(), "Lock must remain held during cross-scan cancellation"
    assert helpers.get_proxy() == "http://127.0.0.1:12345"

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert finished.is_set()
    assert not handlers._scan_lock.locked()
    assert helpers.get_proxy() is None
    assert observations == {
        "initial_proxy": "http://127.0.0.1:12345",
        "late_proxy": "http://127.0.0.1:12345",
        "stdout_restored": False,
    }
