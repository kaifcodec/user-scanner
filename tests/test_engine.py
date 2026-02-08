"""
user-scanner Engine Unit Tests

This suite tests the core orchestration logic of 'engine.py'.
It verifies:
1. Automated mode detection (Email vs Username) based on file paths.
2. Metadata enrichment (Site Name, Category) of Result objects.
3. Execution flow for both sync and async module validation functions.
4. Error handling and result flattening for batch/category scans.

Note: These tests use Mocking and Stubs (via unittest.mock and pytest-monkeypatch)
to isolate the engine from the network. No actual API requests are performed.

"""


import pytest
from types import ModuleType
from user_scanner.core import engine
from unittest.mock import Mock, AsyncMock, call
from user_scanner.core.result import Result


@pytest.fixture
def github_stub():
    module = ModuleType("github")
    module.__file__ = "/some/path/email_scan/dev/github.py"
    return module


@pytest.fixture
def patreon_stub():
    module = ModuleType("patreon")
    module.__file__ = "/some/path/user_scan/creator/patreon.py"
    return module


@pytest.fixture
def medium_stub():
    module = ModuleType("medium")
    module.__file__ = "/some/path/user_scan/creator/medium.py"
    return module


# check
@pytest.mark.anyio
async def test_async_module_func(monkeypatch, github_stub):
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()
    github_stub.validate_github = async_mock

    result = await engine.check(github_stub, "some_email")

    assert result.username == "some_email"
    assert result.is_email is True
    async_mock.assert_awaited_once_with("some_email")


@pytest.mark.anyio
async def test_sync_module_func(github_stub):
    sync_mock = Mock()
    sync_mock.return_value = Result.taken()
    github_stub.validate_github = sync_mock

    result = await engine.check(github_stub, "some_email")

    assert result.username == "some_email"
    assert result.is_email is True
    sync_mock.assert_called_once_with("some_email")


@pytest.mark.anyio
async def test_module_func_raise_exception(github_stub):
    async_mock = AsyncMock()
    async_mock.side_effect = Exception("Exception")
    github_stub.validate_github = async_mock

    result = await engine.check(github_stub, "some_email")

    assert result.username == "some_email"
    assert "Exception" in str(result.reason)
    async_mock.assert_awaited_once()


@pytest.mark.anyio
async def test_missing_validate_func():
    module = ModuleType("github")
    result = await engine.check(module, "some_username")

    assert result.username == "some_username"
    assert "Function validate_github not found" in str(result.reason)


@pytest.mark.anyio
async def test_default_category_email(github_stub):
    github_stub.__file__ = "/some/path/email_scan/github.py"
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()
    github_stub.validate_github = async_mock

    result = await engine.check(github_stub, "some_email")

    assert result.is_email is True
    assert result.category == "Email"


@pytest.mark.anyio
async def test_default_category_username(github_stub):
    github_stub.__file__ = "/some/path/user_scan/github.py"
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()
    github_stub.validate_github = async_mock

    result = await engine.check(github_stub, "some_username")

    assert result.is_email is False
    assert result.category == "Username"


@pytest.mark.anyio
async def test_default_category(monkeypatch, github_stub):
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()
    github_stub.validate_github = async_mock

    monkeypatch.setattr(engine, "find_category", lambda x: "Dev")
    result = await engine.check(github_stub, "some_email")

    assert result.is_email is True
    assert result.category == "Dev"


@pytest.mark.anyio
async def test_metadata_enrichment(patreon_stub):
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()
    patreon_stub.validate_patreon = async_mock

    result = await engine.check(patreon_stub, "some_username")

    assert result.username == "some_username"
    assert result.is_email is False
    assert result.site_name == "Patreon"
    assert result.category == "Creator"


# check_category
@pytest.mark.anyio
async def test_check_category(monkeypatch, patreon_stub, medium_stub):
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()

    monkeypatch.setattr(engine, "load_categories", lambda is_email: {
        "creator": "/fake/path"
    })
    monkeypatch.setattr(engine, "load_modules",
                        lambda x: [patreon_stub, medium_stub])
    monkeypatch.setattr(engine, "check", async_mock)

    result = await engine.check_category("creator", "some_username", is_email=False)
    calls = [call(patreon_stub, "some_username"),
             call(medium_stub, "some_username")]

    assert len(result) == 2
    async_mock.assert_has_calls(calls)


@pytest.mark.anyio
async def test_is_email_passed_correctly(monkeypatch, github_stub):
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()

    sync_mock = Mock()
    sync_mock.return_value = {"dev": "/fake/path"}

    monkeypatch.setattr(engine, "load_categories", sync_mock)
    monkeypatch.setattr(engine, "load_modules", lambda x: [github_stub])
    github_stub.validate_github = async_mock

    result = await engine.check_category("dev", "some_email")

    assert len(result) == 1
    sync_mock.assert_called_once_with(is_email=True)


@pytest.mark.anyio
async def test_case_insensitive_category_match(monkeypatch, github_stub):
    async_mock = AsyncMock()
    async_mock.return_value = Result.taken()

    monkeypatch.setattr(engine, "load_categories", lambda is_email: {
        "dev": "/fake/path"
    })
    monkeypatch.setattr(engine, "load_modules", lambda x: [github_stub])
    github_stub.validate_github = async_mock

    result = await engine.check_category("Dev", "some_email")

    assert len(result) == 1
    async_mock.assert_awaited_once_with("some_email")


@pytest.mark.anyio
async def test_empty_category_list(monkeypatch):
    monkeypatch.setattr(engine, "load_categories", lambda is_email: {
        "dev": "/fake/path"
    })
    monkeypatch.setattr(engine, "load_modules", lambda x: [])
    result = await engine.check_category("dev", "some_email")

    assert result == []


@pytest.mark.anyio
async def test_category_not_found_email(monkeypatch):
    monkeypatch.setattr(engine, "load_categories",
                        lambda is_email: {"dev": "/fake/path"})
    with pytest.raises(ValueError) as exc_info:
        await engine.check_category("unknown", "some_email")

    assert "email_scan" in str(exc_info.value)


@pytest.mark.anyio
async def test_category_not_found_username(monkeypatch):
    monkeypatch.setattr(engine, "load_categories",
                        lambda is_email: {"dev": "/fake/path"})
    with pytest.raises(ValueError) as exc_info:
        await engine.check_category("unknown", "some_username", is_email=False)

    assert "user_scan" in str(exc_info.value)


# check all
@pytest.mark.anyio
async def test_check_all(monkeypatch):
    async_mock = AsyncMock()
    async_mock.return_value = [Result.taken(), Result.available()]
    monkeypatch.setattr(engine, "load_categories", lambda is_email: {
        "creator": "/fake/path",
        "dev": "/fake/path2"
    })
    monkeypatch.setattr(engine, "check_category", async_mock)

    result = await engine.check_all("some_email")
    calls = [call("creator", "some_email", True),
             call("dev", "some_email", True)]

    assert len(result) == 4
    async_mock.assert_has_calls(calls)


@pytest.mark.anyio
async def test_check_all_email_passed_correct(monkeypatch):
    async_mock = AsyncMock()
    async_mock.return_value = [Result.taken(), Result.available()]
    sync_mock = Mock()
    sync_mock.return_value = {
        "creator": "/fake/path",
        "dev": "/fake/path2"
    }

    monkeypatch.setattr(engine, "load_categories", sync_mock)
    monkeypatch.setattr(engine, "check_category", async_mock)

    await engine.check_all("some_username", is_email=False)
    calls = [call("creator", "some_username", False),
             call("dev", "some_username", False)]

    sync_mock.assert_called_once_with(is_email=False)
    async_mock.assert_has_calls(calls, any_order=False)


@pytest.mark.anyio
async def test_check_all_nested_lis_flatten(monkeypatch):
    async_mock = AsyncMock()
    async_mock.side_effect = [[Result.taken(), Result.available()],
                              [Result.taken()]]
    monkeypatch.setattr(engine, "load_categories", lambda is_email: {
        "creator": "/fake/path",
        "dev": "/fake/path2"
    })
    monkeypatch.setattr(engine, "check_category", async_mock)

    result = await engine.check_all("some_email")

    assert len(result) == 3


@pytest.mark.anyio
async def test_check_all_category_exception(monkeypatch):
    async def check_category_side_effect(cat_name, target, is_email=True):
        if cat_name == "dev":
            raise ValueError("Failed")
        return [Result.taken(), Result.available()]

    monkeypatch.setattr(engine, "load_categories", lambda is_email: {
        "creator": "/fake/path",
        "dev": "/fake/path2"
    })
    monkeypatch.setattr(engine, "check_category", check_category_side_effect)

    with pytest.raises(ValueError) as exc_info:
        await engine.check_all("some_email")

    assert "Failed" in str(exc_info.value)
