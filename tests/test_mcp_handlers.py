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
async def test_execute_scan_invalid_concurrency():
    from user_scanner.mcp.handlers import _scan_lock

    for invalid_c in [0, -1, -10]:
        with pytest.raises(ValueError, match="Concurrency must be at least 1"):
            await execute_scan({"username": "testuser", "concurrency": invalid_c}, is_email=False)
        assert not _scan_lock.locked()

    with pytest.raises(ValueError, match="Invalid concurrency value"):
        await execute_scan({"username": "testuser", "concurrency": "not_an_int"}, is_email=False)
    assert not _scan_lock.locked()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "arguments, message",
    [
        ({"timeout": 0}, "greater than 0"),
        ({"timeout": -1}, "greater than 0"),
        ({"timeout": float("nan")}, "finite"),
        ({"timeout": float("inf")}, "finite"),
        ({"timeout": 99999}, "at most"),
        ({"cross_depth": 0}, "at least 1"),
        ({"cross_sweep": -1}, "at least 0"),
        ({"concurrency": True}, "Invalid concurrency value"),
        ({"concurrency": 501}, "must be at most 500"),
        ({"concurrency": 10**18}, "must be at most 500"),
        ({"concurrency": "501"}, "must be at most 500"),
    ],
)
async def test_execute_scan_rejects_out_of_range_numbers(arguments, message):
    from user_scanner.mcp.handlers import _scan_lock

    with pytest.raises(ValueError, match=message):
        await execute_scan({"username": "testuser", **arguments}, is_email=False)
    assert not _scan_lock.locked()


@pytest.mark.anyio
async def test_execute_scan_unknown_module_is_an_error():
    from user_scanner.mcp.handlers import _scan_lock

    with pytest.raises(ValueError, match="Unknown username module 'githb'") as exc_info:
        await execute_scan({"username": "testuser", "module": "githb"}, is_email=False)
    assert "Did you mean: 'github'" in str(exc_info.value)
    assert "list_available_modules" in str(exc_info.value)
    assert not _scan_lock.locked()

    with pytest.raises(ValueError, match="Unknown email module 'no_such_site_xyz'") as exc_info:
        await execute_scan({"email": "test@example.com", "module": "no_such_site_xyz"}, is_email=True)
    assert "Did you mean" not in str(exc_info.value)
    assert "list_available_modules" in str(exc_info.value)
    assert not _scan_lock.locked()


@pytest.mark.anyio
async def test_execute_scan_unknown_category_is_an_error():
    from user_scanner.mcp.handlers import _scan_lock

    # Category names are exact, like the CLI: a different-case spelling is
    # rejected and the correctly cased name is the first suggestion.
    with pytest.raises(ValueError, match="Unknown username category 'Social'") as exc_info:
        await execute_scan({"username": "testuser", "category": "Social"}, is_email=False)
    assert "Did you mean: 'social'" in str(exc_info.value)
    assert not _scan_lock.locked()

    with pytest.raises(ValueError, match="Unknown email category 'gamming'") as exc_info:
        await execute_scan({"email": "test@example.com", "category": "gamming"}, is_email=True)
    assert "'gaming'" in str(exc_info.value)
    assert not _scan_lock.locked()


@pytest.mark.anyio
async def test_execute_scan_unknown_category_respects_no_nsfw():
    # 'adult' exists, but not once no_nsfw excludes it
    with pytest.raises(ValueError, match="Unknown username category 'adult'"):
        await execute_scan(
            {"username": "testuser", "category": "adult", "no_nsfw": True}, is_email=False
        )


@pytest.mark.anyio
@patch("user_scanner.mcp.handlers._run_scan")
@patch("user_scanner.mcp.handlers.set_proxy_manager")
async def test_execute_scan_unknown_scope_never_starts_a_scan(mock_set_proxy, mock_run_scan):
    with pytest.raises(ValueError, match="Unknown username module"):
        await execute_scan(
            {"username": "testuser", "module": "githb", "proxies": ["http://127.0.0.1:8080"]},
            is_email=False,
        )
    mock_set_proxy.assert_not_called()
    mock_run_scan.assert_not_called()


@pytest.mark.anyio
@patch("user_scanner.mcp.handlers._run_scan")
async def test_execute_scan_known_scopes_still_run(mock_run_scan):
    mock_run_scan.return_value = [Result.available()]

    # Module names resolve case-insensitively, exactly like the CLI's -m flag
    await execute_scan({"username": "testuser", "module": "GitHub"}, is_email=False)
    assert mock_run_scan.call_args[0][4] == "GitHub"

    await execute_scan({"username": "testuser", "category": "social"}, is_email=False)
    assert mock_run_scan.call_args[0][3] == "social"

    await execute_scan({"email": "test@example.com", "module": "github"}, is_email=True)
    assert mock_run_scan.call_args[0][4] == "github"


def test_run_scan_rejects_unknown_scope():
    """The thread-side scan must not quietly return [] for a bad scope either."""
    from user_scanner.mcp.handlers import _run_scan

    config = ScanConfig(allow_loud=False, no_nsfw=False, timeout=None)
    with pytest.raises(ValueError, match="Unknown username module 'githb'"):
        _run_scan("testuser", config, False, None, "githb")
    with pytest.raises(ValueError, match="Unknown email category 'gamming'"):
        _run_scan("test@example.com", config, True, "gamming", None)


def test_tool_schema_concurrency_minimum():
    from user_scanner.mcp.schemas import get_tool_list

    tools = get_tool_list()
    scan_tools = [t for t in tools if t.name in ("scan_username", "scan_email")]
    assert len(scan_tools) == 2
    for t in scan_tools:
        conc_prop = t.inputSchema["properties"]["concurrency"]
        assert conc_prop["type"] == "integer"
        assert conc_prop["minimum"] == 1
        assert conc_prop["maximum"] == 500
        props = t.inputSchema["properties"]
        assert props["timeout"]["exclusiveMinimum"] == 0
        assert props["timeout"]["maximum"] == 3600
        assert props["cross_depth"]["minimum"] == 1
        assert props["cross_sweep"]["minimum"] == 0


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
    
    # Passing a module name with a dot (e.g. from the list_available_modules output).
    # Made.porn is an email module, so scan as email: a name that resolves to
    # nothing is an error now.
    arguments = {
        "email": "test@example.com",
        "module": "Made.porn", 
    }
    
    await execute_scan(arguments, is_email=True)
    
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
