import pytest
from user_scanner.core.result import Result
from user_scanner.core.formatter import into_pdf
from user_scanner.core.pdf_generator import generate_pdf_report, REPORTLAB_AVAILABLE


@pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab not installed")
def test_generate_pdf_report_basic():
    results = [
        Result.taken(
            site_name="GitHub",
            category="Dev",
            url="https://github.com/testuser",
            extra={
                "name": "Test User",
                "bio": "Open Source Developer",
                "followers": "100",
                "avatar": "https://avatars.githubusercontent.com/u/1?v=4",
            },
        ),
        Result.available(site_name="Twitter", category="Social", url="https://twitter.com/testuser"),
    ]

    pdf_bytes = generate_pdf_report(
        target="testuser",
        scan_type="Username",
        results=results,
        total_modules=2,
        include_media=True,
        version="1.4.1.9",
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab not installed")
def test_formatter_into_pdf():
    results = [
        Result.taken(
            site_name="GitHub",
            category="Dev",
            url="https://github.com/testuser",
            extra={"name": "Test User"},
        )
    ]

    pdf_bytes = into_pdf(
        results=results,
        target="testuser@gmail.com",
        scan_type="Email",
        total_modules=10,
        include_media=False,
        version="1.4.1.9",
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab not installed")
def test_generate_pdf_report_ampersand_url():
    results = [
        Result.taken(
            site_name="Snapchat",
            category="Social",
            url="https://app.snapchat.com/web/deeplink/snapcode?username=asdfg&type=SVG&bitmoji=enable",
            extra={
                "snapcode": "https://app.snapchat.com/web/deeplink/snapcode?username=asdfg&type=SVG&bitmoji=enable"
            },
        )
    ]

    pdf_bytes = generate_pdf_report(
        target="asdfg",
        scan_type="Username",
        results=results,
        total_modules=1,
        include_media=False,
        version="1.4.1.9",
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_no_reportlab_import_error(monkeypatch):
    import user_scanner.core.pdf_generator as pdf_gen

    monkeypatch.setattr(pdf_gen, "REPORTLAB_AVAILABLE", False)

    with pytest.raises(ImportError) as exc_info:
        generate_pdf_report("target", "Username", [])

    assert "ReportLab is required for PDF generation" in str(exc_info.value)


def test_fetch_and_resize_image_routes_through_proxy(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from user_scanner.core.helpers import set_proxy_manager, set_global_timeout
    from user_scanner.core.pdf_generator import fetch_and_resize_image

    recorded_kwargs = {}

    def mock_get(url, **kwargs):
        recorded_kwargs.update(kwargs)
        resp = MagicMock()
        resp.status_code = 404
        return resp

    monkeypatch.setattr(httpx, "get", mock_get)

    try:
        set_proxy_manager(proxies=["http://10.0.0.1:8080"])
        set_global_timeout(7.5)

        res = fetch_and_resize_image("https://example.com/avatar.png")
        assert res is None
        assert recorded_kwargs.get("proxy") == "http://10.0.0.1:8080"
        assert recorded_kwargs.get("timeout") == 7.5
    finally:
        set_proxy_manager(proxies=None)
        set_global_timeout(None)


def test_fetch_and_resize_image_no_proxy(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from user_scanner.core.helpers import set_proxy_manager, set_global_timeout
    from user_scanner.core.pdf_generator import fetch_and_resize_image

    recorded_kwargs = {}

    def mock_get(url, **kwargs):
        recorded_kwargs.update(kwargs)
        resp = MagicMock()
        resp.status_code = 404
        return resp

    monkeypatch.setattr(httpx, "get", mock_get)

    set_proxy_manager(proxies=None)
    set_global_timeout(None)

    res = fetch_and_resize_image("https://example.com/avatar.png")
    assert res is None
    assert recorded_kwargs.get("proxy") is None
    assert recorded_kwargs.get("timeout") == 5.0


def test_fetch_and_resize_image_proxy_failure_returns_none(monkeypatch):
    import httpx
    from user_scanner.core.helpers import set_proxy_manager
    from user_scanner.core.pdf_generator import fetch_and_resize_image

    def mock_get(url, **kwargs):
        raise httpx.ProxyError("Proxy connection refused")

    monkeypatch.setattr(httpx, "get", mock_get)

    try:
        set_proxy_manager(proxies=["http://10.0.0.1:8080"])
        res = fetch_and_resize_image("https://example.com/avatar.png")
        assert res is None
    finally:
        set_proxy_manager(proxies=None)

