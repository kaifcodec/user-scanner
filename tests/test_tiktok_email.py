import pytest
from unittest.mock import AsyncMock, patch
from user_scanner.email_scan.social.tiktok import validate_tiktok
from user_scanner.core.result import Status

@pytest.mark.asyncio
async def test_validate_tiktok_taken():
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"data": {"is_registered": true}}'
    mock_resp.json.return_value = {"data": {"is_registered": True}}
    
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        result = await validate_tiktok("test@example.com")
        assert result.status == Status.TAKEN

@pytest.mark.asyncio
async def test_validate_tiktok_available():
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"data": {"is_registered": false}}'
    mock_resp.json.return_value = {"data": {"is_registered": False}}
    
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        result = await validate_tiktok("test@example.com")
        assert result.status == Status.AVAILABLE

@pytest.mark.asyncio
async def test_validate_tiktok_captcha():
    mock_resp = AsyncMock()
    mock_resp.status_code = 403
    mock_resp.text = "verify with captcha"
    
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        result = await validate_tiktok("test@example.com")
        assert result.status == Status.ERROR
        assert "CAPTCHA-protected" in result.get_reason()

@pytest.mark.asyncio
async def test_validate_tiktok_error():
    mock_resp = AsyncMock()
    mock_resp.status_code = 500
    
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        result = await validate_tiktok("test@example.com")
        assert result.status == Status.ERROR
        assert "Unexpected status code" in result.get_reason()
