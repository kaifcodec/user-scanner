import pytest

pytest.importorskip("starlette")
pytest.importorskip("jinja2")
pytest.importorskip("sse_starlette")

from starlette.testclient import TestClient
from user_scanner.web.server import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture(autouse=True)
def seed_test_session():
    from user_scanner.web.session import save_scan_session
    save_scan_session("case-synthetic-user", {
        "case_id": "case-synthetic-user",
        "target": "test_user",
        "threat_actor": "test_user",
        "title": "Synthetic OSINT Benchmark: @test_user",
        "category": "DEV",
        "total_modules": 450,
        "total_hits": 2,
        "elements": [
            {"data": {"id": "actor_root", "label": "Target: @test_user", "type": "TARGET"}},
            {"data": {"id": "plat_dev", "label": "GitHub", "type": "SOCIAL_ACCOUNT", "category": "DEV", "url": "https://github.com/test_user"}},
            {"data": {"id": "e1", "source": "actor_root", "target": "plat_dev", "relation": "REGISTERED_ON"}}
        ],
        "raw_results": [
            {"status": "Found", "username": "test_user", "site_name": "GitHub", "category": "DEV", "url": "https://github.com/test_user", "extra": {}, "media": {}},
            {"status": "Found", "username": "test_user", "site_name": "Twitter / X", "category": "SOCIAL", "url": "https://x.com/test_user", "extra": {}, "media": {}}
        ]
    })

def test_web_index_route(client):
    res = client.get("/?u=testuser")
    assert res.status_code == 200
    assert "USER" in res.text
    assert "-SCANNER" in res.text
    assert "dashboard.css" in res.text
    assert "graph.js" in res.text
    assert "dashboard.js" in res.text
    assert "cy" in res.text

def test_web_cases_api(client):
    res = client.get("/api/cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) >= 1
    assert any(c["case_id"] == "case-synthetic-user" for c in cases)

def test_web_case_detail_api(client):
    res = client.get("/api/cases/case-synthetic-user")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "case-synthetic-user"
    assert len(data["elements"]) > 0

def test_web_stix_route_removed(client):
    res = client.get("/api/export/stix/case-synthetic-user")
    assert res.status_code == 404

def test_web_csv_export(client):
    res = client.get("/api/export/csv/case-synthetic-user")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "username,category,site_name,status,url,extra,media,reason" in res.text
    assert "test_user,DEV,GitHub,Found" in res.text

def test_web_json_export(client):
    res = client.get("/api/export/json/case-synthetic-user")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(item.get("site_name") == "GitHub" and item.get("status") == "Found" for item in data)
    assert any(item.get("category") == "DEV" for item in data)

def test_web_static_mounts(client):
    res_css = client.get("/static/css/dashboard.css")
    assert res_css.status_code == 200

    res_graph = client.get("/static/js/graph.js")
    assert res_graph.status_code == 200

    res_dash = client.get("/static/js/dashboard.js")
    assert res_dash.status_code == 200

def test_web_scan_stream_empty(client):
    res = client.get("/api/scan/stream")
    assert res.status_code == 200
    assert "event" in res.text
    assert "error" in res.text

def test_web_modules_api(client):
    res = client.get("/api/modules?is_email=false")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_categories"] > 0
    assert "DEV" in data["categories"]

def test_web_proxies_validate_api(client):
    res = client.post("/api/proxies/validate", json={"proxies": ["http://127.0.0.1:9999"]})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_tested"] == 1

def test_web_hudson_api_missing(client):
    res = client.get("/api/hudson/check")
    assert res.status_code == 400

def test_web_pdf_export(client, monkeypatch):
    monkeypatch.setattr(
        "user_scanner.core.formatter.into_pdf",
        lambda **kwargs: b"%PDF-1.4 mock pdf content"
    )
    res = client.get("/api/export/pdf/case-synthetic-user")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

def test_web_pdf_export_missing_dependency(client, monkeypatch):
    def mock_fail(**kwargs):
        raise ImportError("ReportLab is required for PDF generation.")
    monkeypatch.setattr("user_scanner.core.formatter.into_pdf", mock_fail)
    res = client.get("/api/export/pdf/case-synthetic-user")
    assert res.status_code == 500
    assert "ReportLab is required" in res.json()["message"]

def test_web_template_cli_parity_elements(client):
    res = client.get("/")
    assert res.status_code == 200
    # Dedicated Mode Navigation
    assert "tab-btn-user-scan" in res.text
    assert "tab-btn-email-scan" in res.text
    assert "section-user-scan" in res.text
    assert "section-email-scan" in res.text
    # Username subtabs & inputs
    assert "user-subtab-single" in res.text
    assert "user-subtab-bulk" in res.text
    assert "scan-user-target" in res.text
    assert "scan-user-bulk-targets" in res.text
    assert "file-user-bulk-targets" in res.text
    assert "user-module-search-input" in res.text
    assert "user-selected-modules" in res.text
    assert "user-category-chips-group" in res.text
    # Email subtabs & inputs
    assert "email-subtab-single" in res.text
    assert "email-subtab-bulk" in res.text
    assert "scan-email-target" in res.text
    assert "scan-email-bulk-targets" in res.text
    assert "file-email-bulk-targets" in res.text
    assert "email-module-search-input" in res.text
    assert "email-selected-modules" in res.text
    assert "email-category-chips-group" in res.text
    # Master toggle & Accordion OPSEC controls
    assert "adv-accordion-toggle" in res.text
    assert "cfg-master-advanced-toggle" in res.text
    assert "adv-controls-group" in res.text
    assert "cfg-allow-loud" in res.text
    assert "cfg-no-nsfw" in res.text
    assert "cfg-show-all" in res.text
    # Network tuning & proxies
    assert "cfg-concurrency" in res.text
    assert "cfg-timeout" in res.text
    assert "cfg-delay" in res.text
    assert "btn-validate-proxies" in res.text
    # Cross-Scan & Hudson Rock
    assert "cfg-cross-scan" in res.text
    assert "cfg-cross-depth" in res.text
    assert "cfg-hudson-scan" in res.text
    # PDF export & Hudson tab
    assert "btn-pdf-export" in res.text
    assert "tab-hudson" in res.text

def test_web_scan_stream_post_options(client):
    # Test POST payload parsing in scan stream
    res = client.post("/api/scan/stream", json={
        "targets": ["investigation_test_alpha"],
        "scan_type": "username",
        "category": "DEV",
        "modules": ["github"],
        "allow_loud": True,
        "no_nsfw": True,
        "show_all": False,
        "timeout": 5.0,
        "concurrency": 10,
        "delay": 0.0,
        "cross_scan": False,
        "hudson_scan": False
    })
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    first_chunk = res.text
    assert "event" in first_chunk
    assert "init" in first_chunk

def test_web_cross_scan_email_pivot_triggers_scan(client, monkeypatch):
    from user_scanner.core.result import Result

    email_scanned_targets = []

    async def mock_user_worker(module, target, sem, configs, cat_override=None):
        # Return a verified account that exposes an email pivot
        return Result.taken(
            username=target,
            site_name="MockGit",
            extra={"email": "discovered_target@gmail.com"}
        )

    async def mock_email_worker(module, email, sem, configs, cat_override=None):
        email_scanned_targets.append(email)
        return Result.taken(
            username=email,
            site_name="MockPlatform",
            extra={"status": "registered"}
        )

    monkeypatch.setattr("user_scanner.web.routes.api._user_async_worker", mock_user_worker)
    monkeypatch.setattr("user_scanner.web.routes.api._email_async_worker", mock_email_worker)

    res = client.post("/api/scan/stream", json={
        "targets": ["primary_tester"],
        "scan_type": "username",
        "modules": ["github"],
        "cross_scan": True,
        "cross_depth": 1,
        "cross_sweep": 3,
        "cross_links": "all",
        "cross_emails": "all"
    })
    assert res.status_code == 200
    text = res.text

    # Verify primary scan completed
    assert "discovered_target@gmail.com" in text
    # Verify cross_round event was emitted targeting the discovered email
    assert "cross_round" in text
    assert '"target_type": "email"' in text or '"target": "discovered_target@gmail.com"' in text
    # Verify that email worker actually scanned the discovered email
    assert "discovered_target@gmail.com" in email_scanned_targets

def test_web_loud_modules_filtered_by_default(client):
    # When allow_loud is False, requesting a loud module should skip it
    res = client.post("/api/scan/stream", json={
        "targets": ["investigation_test_alpha"],
        "scan_type": "email",
        "modules": ["netflix"],
        "allow_loud": False
    })
    assert res.status_code == 200
    text = res.text
    # Should complete without querying netflix hit because netflix is loud
    assert "init" in text
    assert "complete" in text

def test_web_cross_scan_username_pivot_triggers_scan(client, monkeypatch):
    from user_scanner.core.result import Result

    user_scanned_targets = []

    async def mock_email_worker(module, email, sem, configs, cat_override=None):
        return Result.taken(
            username=email,
            site_name="MockMailSite",
            extra={"links": "https://github.com/discovered_handle"}
        )

    async def mock_user_worker(module, target, sem, configs, cat_override=None):
        user_scanned_targets.append(target)
        return Result.taken(
            username=target,
            site_name="MockSocial",
            extra={"status": "active"}
        )

    monkeypatch.setattr("user_scanner.web.routes.api._email_async_worker", mock_email_worker)
    monkeypatch.setattr("user_scanner.web.routes.api._user_async_worker", mock_user_worker)

    res = client.post("/api/scan/stream", json={
        "targets": ["email_lead@domain.com"],
        "scan_type": "email",
        "modules": ["gravatar"],
        "cross_scan": True,
        "cross_depth": 1,
        "cross_sweep": 3,
        "cross_links": "all",
        "cross_emails": "all"
    })
    assert res.status_code == 200
    text = res.text

    assert "cross_round" in text
    assert "discovered_handle" in user_scanned_targets


def test_web_exports_from_live_scan(client, monkeypatch):
    from user_scanner.web.session import save_backup

    case_id = "test-live-case-export"
    case_data = {
        "case_id": case_id,
        "threat_actor": "live_investigation_lead",
        "scan_type": "Cross-Scan (Username)",
        "total_modules": 529,
        "raw_results": [
            {
                "status": "Found",
                "reason": "",
                "username": "live_investigation_lead",
                "site_name": "GitHub",
                "category": "DEV",
                "url": "https://github.com/live_investigation_lead",
                "extra": {"bio": "Lead researcher", "email": "lead@research.org"},
                "media": {"avatar": "https://avatars.githubusercontent.com/u/99999"}
            },
            {
                "status": "Registered",
                "reason": "",
                "username": "lead@research.org",
                "site_name": "Gravatar",
                "category": "EMAIL",
                "url": "https://gravatar.com/lead",
                "extra": {},
                "media": {}
            }
        ],
        "elements": []
    }
    save_backup(case_id, case_data)

    monkeypatch.setattr(
        "user_scanner.core.formatter.into_pdf",
        lambda **kwargs: b"%PDF-1.4 mock pdf content"
    )

    # 1. Test PDF Export
    pdf_res = client.get(f"/api/export/pdf/{case_id}")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")
    assert "report_live_investigation_lead_test-live-case-export.pdf" in pdf_res.headers["content-disposition"]

    # 2. Test CSV Export
    csv_res = client.get(f"/api/export/csv/{case_id}")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "username,category,site_name,status,url,extra,media,reason" in csv_res.text
    assert "live_investigation_lead,DEV,GitHub,Found" in csv_res.text
    assert "lead@research.org,EMAIL,Gravatar,Registered" in csv_res.text

    # 3. Test JSON Export
    json_res = client.get(f"/api/export/json/{case_id}")
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    items = json_res.json()
    assert isinstance(items, list)
    assert len(items) == 2
    assert items[0]["site_name"] == "GitHub"
    assert items[1]["site_name"] == "Gravatar"


def test_web_progress_event_telemetry(client, monkeypatch):
    import json
    from user_scanner.core.result import Result

    async def mock_user_worker(module, target, sem, configs, cat_override=None):
        return Result.taken(
            username=target,
            site_name="MockSite",
            extra={"bio": "Test bio"}
        )

    monkeypatch.setattr("user_scanner.web.routes.api._user_async_worker", mock_user_worker)

    res = client.post("/api/scan/stream", json={
        "targets": ["telemetry_lead"],
        "scan_type": "username",
        "modules": ["github", "gitlab"],
    })
    assert res.status_code == 200
    events = []
    for line in res.text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    init_ev = next((e for e in events if e.get("event") == "init"), None)
    assert init_ev is not None
    assert "total_modules" in init_ev
    assert "total_checks" in init_ev
    assert init_ev["total_modules"] >= 2

    progress_evs = [e for e in events if e.get("event") == "progress"]
    assert len(progress_evs) >= 1
    prog = progress_evs[-1]
    assert "checked" in prog
    assert "total" in prog
    assert "remaining" in prog
    assert "percent" in prog
    assert "target" in prog
    assert "found" in prog
    assert prog["checked"] >= 2
    assert prog["remaining"] == 0
    assert prog["percent"] == 100.0


def test_web_template_progress_and_lock_elements(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    # Progress Dock
    assert "scan-progress-dock" in html
    assert "dock-radar-beacon" in html
    assert "dock-status-text" in html
    assert "dock-target-badge" in html
    assert "dock-counts-text" in html
    assert "dock-remaining-text" in html
    assert "dock-percent-text" in html
    assert "btn-dock-stop" in html
    assert "btn-dock-export" in html
    assert "btn-dock-close" in html
    # Telemetry card progress bar
    assert "telemetry-progress-container" in html
    assert "telemetry-progress-percent" in html
    assert "telemetry-progress-fill" in html
    # Export locking elements
    assert "export-status-card" in html
    assert "export-status-badge" in html
    assert "export-status-title" in html
    assert "is-locked" in html
    assert "btn-lock-indicator" in html


def test_web_export_preseeded_backup(client, monkeypatch):
    import json
    from user_scanner.core.result import Result

    async def mock_user_worker(module, target, sem, configs, cat_override=None):
        return Result.taken(
            username=target,
            site_name="MockSite",
            extra={}
        )

    monkeypatch.setattr("user_scanner.web.routes.api._user_async_worker", mock_user_worker)

    res = client.post("/api/scan/stream", json={
        "targets": ["preseed_test_lead"],
        "scan_type": "username",
        "modules": ["github"],
    })
    assert res.status_code == 200
    # Extract case_id from init
    case_id = None
    for line in res.text.splitlines():
        if line.startswith("data: "):
            ev = json.loads(line[6:])
            if ev.get("event") == "init":
                case_id = ev["case_id"]
                break

    assert case_id is not None
    from user_scanner.web.session import get_backup
    backup = get_backup(case_id)
    assert backup is not None
    assert backup["threat_actor"] == "preseed_test_lead"

    json_res = client.get(f"/api/export/json/{case_id}")
    assert json_res.status_code == 200


def test_web_scan_stream_unresolvable_modules(client):
    res = client.post("/api/scan/stream", json={
        "targets": ["testuser"],
        "scan_type": "username",
        "modules": ["fake_nonexistent_mod_xyz"],
    })
    assert res.status_code == 200
    assert '"event": "error"' in res.text
    assert "not found for username scan" in res.text


def test_web_scan_stream_handles_at_prefix_and_domain_suffix(client, monkeypatch):
    from user_scanner.core.result import Result

    scanned_targets = []

    async def mock_user_worker(module, target, sem, configs, cat_override=None):
        scanned_targets.append(target)
        return Result.available()

    monkeypatch.setattr("user_scanner.web.routes.api._user_async_worker", mock_user_worker)

    res = client.post("/api/scan/stream", json={
        "targets": ["@testuser"],
        "scan_type": "username",
        "modules": ["instagram.com"],
    })
    assert res.status_code == 200
    assert "init" in res.text
    assert "complete" in res.text
    assert "testuser" in scanned_targets


def test_web_sponsor_integration_elements(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Top navigation sponsor pill
    assert "sponsor-nav-btn" in html
    assert "https://github.com/sponsors/kaifcodec" in html

    # 2. Floating scan progress dock sponsor action
    assert "btn-dock-sponsor" in html
    assert "dock-btn-sponsor" in html

    # 3. Export drawer sponsor card
    assert "sponsor-drawer-card" in html
    assert "btn-sponsor-action" in html
    assert "Support Active Development" in html




