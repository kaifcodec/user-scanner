import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from user_scanner.email_scan.social.tiktok import validate_tiktok
from user_scanner.core.result import Status

@pytest.mark.asyncio
async def test_validate_tiktok_taken():
    # Mock the response for the POST request to the password reset API
    mock_get_resp = AsyncMock()
    mock_get_resp.status_code = 200

    mock_post_resp = AsyncMock()
    mock_post_resp.status_code = 200
    mock_post_resp.text = '{"email": {"is_registered": true}, "error_code": 0}'
    mock_post_resp.json.return_value = {"email": {"is_registered": True}, "error_code": 0}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_get_resp
        mock_client.post.return_value = mock_post_resp
        mock_client_class.return_value = mock_client

        result = await validate_tiktok("test@example.com")
        assert result.status == Status.TAKEN

@pytest.mark.asyncio
async def test_validate_tiktok_available():
    # Mock the response for the POST request to the password reset API
    mock_get_resp = AsyncMock()
    mock_get_resp.status_code = 200

    mock_post_resp = AsyncMock()
    mock_post_resp.status_code = 200
    mock_post_resp.text = '{"email": {"is_registered": false}, "error_code": 0}'
    mock_post_resp.json.return_value = {"email": {"is_registered": False}, "error_code": 0}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_get_resp
        mock_client.post.return_value = mock_post_resp
        mock_client_class.return_value = mock_client

        result = await validate_tiktok("test@example.com")
        assert result.status == Status.AVAILABLE

@pytest.mark.asyncio
async def test_validate_tiktok_captcha():
    # Mock the response showing captcha protection
    mock_get_resp = AsyncMock()
    mock_get_resp.status_code = 200

    mock_post_resp = AsyncMock()
    mock_post_resp.status_code = 200
    mock_post_resp.text = '{"error_code": 20001, "captcha": "required"}'
    mock_post_resp.json.return_value = {"error_code": 20001, "captcha": "required"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_get_resp
        mock_client.post.return_value = mock_post_resp
        mock_client_class.return_value = mock_client

        result = await validate_tiktok("test@example.com")
        assert result.status == Status.ERROR
        assert "CAPTCHA" in result.get_reason()

@pytest.mark.asyncio
async def test_validate_tiktok_bot_detection():
    # Mock the response for bot detection (error_code 0 without is_registered flag)
    mock_get_resp = AsyncMock()
    mock_get_resp.status_code = 200

    mock_post_resp = AsyncMock()
    mock_post_resp.status_code = 200
    mock_post_resp.text = '{"error_code": 0, "verify": "some_verification_needed"}'
    mock_post_resp.json.return_value = {"error_code": 0, "verify": "some_verification_needed"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_get_resp
        mock_client.post.return_value = mock_post_resp
        mock_client_class.return_value = mock_client

        result = await validate_tiktok("test@example.com")
        assert result.status == Status.ERROR
        assert "bot" in result.get_reason().lower()
