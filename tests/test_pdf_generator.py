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
