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
