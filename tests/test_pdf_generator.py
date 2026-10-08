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
    import user_scanner.core.pdf_generator as pdf_gen
    from user_scanner.core.helpers import set_proxy_manager, set_global_timeout
    from user_scanner.core.pdf_generator import fetch_and_resize_image

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", True)
    recorded_kwargs = {}

    def mock_get(url, **kwargs):
        recorded_kwargs.update(kwargs)
        resp = MagicMock()
        resp.is_redirect = False
        resp.status_code = 404
        return resp

    monkeypatch.setattr(httpx, "get", mock_get)

    try:
        set_proxy_manager(proxies=["http://10.0.0.1:8080"])
        set_global_timeout(7.5)

        res = fetch_and_resize_image("https://8.8.8.8/avatar.png")
        assert res is None
        assert recorded_kwargs.get("proxy") == "http://10.0.0.1:8080"
        assert recorded_kwargs.get("timeout") == 7.5
    finally:
        set_proxy_manager(proxies=None)
        set_global_timeout(None)


def test_fetch_and_resize_image_no_proxy(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    import user_scanner.core.pdf_generator as pdf_gen
    from user_scanner.core.helpers import set_proxy_manager, set_global_timeout
    from user_scanner.core.pdf_generator import fetch_and_resize_image

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", True)
    recorded_kwargs = {}

    def mock_get(url, **kwargs):
        recorded_kwargs.update(kwargs)
        resp = MagicMock()
        resp.is_redirect = False
        resp.status_code = 404
        return resp

    monkeypatch.setattr(httpx, "get", mock_get)

    set_proxy_manager(proxies=None)
    set_global_timeout(None)

    res = fetch_and_resize_image("https://8.8.8.8/avatar.png")
    assert res is None
    assert recorded_kwargs.get("proxy") is None
    assert recorded_kwargs.get("timeout") == 5.0


def test_fetch_and_resize_image_proxy_failure_returns_none(monkeypatch):
    import httpx
    import user_scanner.core.pdf_generator as pdf_gen
    from user_scanner.core.helpers import set_proxy_manager
    from user_scanner.core.pdf_generator import fetch_and_resize_image

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", True)

    def mock_get(url, **kwargs):
        raise httpx.ProxyError("Proxy connection refused")

    monkeypatch.setattr(httpx, "get", mock_get)

    try:
        set_proxy_manager(proxies=["http://10.0.0.1:8080"])
        res = fetch_and_resize_image("https://8.8.8.8/avatar.png")
        assert res is None
    finally:
        set_proxy_manager(proxies=None)


@pytest.mark.parametrize(
    "unsafe_url",
    [
        "http://127.0.0.1/avatar.png",
        "http://localhost/avatar.png",
        "http://[::1]/avatar.png",
        "http://10.0.0.1/avatar.png",
        "http://192.168.1.1/avatar.png",
        "http://172.16.0.1/avatar.png",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0/avatar.png",
        "file:///etc/passwd",
        "ftp://example.com/avatar.png",
        "gopher://127.0.0.1:70/",
        "javascript:alert(1)",
    ],
)
def test_is_safe_media_url_rejects_unsafe_destinations(unsafe_url):
    from user_scanner.core.pdf_generator import is_safe_media_url

    assert is_safe_media_url(unsafe_url) is False


@pytest.mark.parametrize(
    "safe_url",
    [
        "http://8.8.8.8/avatar.png",
        "http://1.1.1.1/avatar.png",
        "https://8.8.8.8/avatar.png",
    ],
)
def test_is_safe_media_url_accepts_public_ips(safe_url):
    from user_scanner.core.pdf_generator import is_safe_media_url

    assert is_safe_media_url(safe_url) is True


def test_fetch_and_resize_image_rejects_loopback(monkeypatch):
    import user_scanner.core.pdf_generator as pdf_gen

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", True)
    res = pdf_gen.fetch_and_resize_image("http://127.0.0.1:8080/avatar.png")
    assert res is None


def test_fetch_and_resize_image_rejects_redirect_to_private(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    import user_scanner.core.pdf_generator as pdf_gen

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", True)

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.is_redirect = True
        resp.status_code = 302
        resp.headers = {"Location": "http://127.0.0.1:9000/internal-pfp"}
        return resp

    monkeypatch.setattr(httpx, "get", mock_get)

    res = pdf_gen.fetch_and_resize_image("http://8.8.8.8/avatar.png")
    assert res is None


def test_fetch_and_resize_image_follows_safe_redirect(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    import user_scanner.core.pdf_generator as pdf_gen

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", True)
    urls_requested = []

    def mock_get(url, **kwargs):
        urls_requested.append(url)
        resp = MagicMock()
        if url == "http://8.8.8.8/initial":
            resp.is_redirect = True
            resp.status_code = 302
            resp.headers = {"Location": "http://1.1.1.1/final.png"}
        else:
            resp.is_redirect = False
            resp.status_code = 404
        return resp

    monkeypatch.setattr(httpx, "get", mock_get)

    res = pdf_gen.fetch_and_resize_image("http://8.8.8.8/initial")
    assert res is None
    assert urls_requested == ["http://8.8.8.8/initial", "http://1.1.1.1/final.png"]


def test_fetch_and_resize_image_without_pil_returns_none(monkeypatch):
    import user_scanner.core.pdf_generator as pdf_gen

    monkeypatch.setattr(pdf_gen, "PIL_AVAILABLE", False)
    assert pdf_gen.fetch_and_resize_image("https://8.8.8.8/avatar.png") is None


@pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab not installed")
def test_pdf_fetches_loopback_media_and_redirect_blocked():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from PIL import Image as PILImage
    import threading
    import io

    image = io.BytesIO()
    PILImage.new("RGB", (2, 2), "red").save(image, format="PNG")
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/private-image")
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(image.getvalue())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        result = Result.taken(site_name="Example", username="audit", media={"avatar": base + "/redirect"})
        data = generate_pdf_report("audit", "Username", [result])
        assert data.startswith(b"%PDF-")
        assert seen == []  # Loopback server must NEVER be contacted!
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


