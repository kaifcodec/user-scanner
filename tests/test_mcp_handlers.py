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
