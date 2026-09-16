"""Starlette / Uvicorn Server for user-scanner OSINT Workbench."""
import os
from typing import Optional
import webbrowser
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from user_scanner.web.routes.ui import index_view
from user_scanner.web.routes.api import (
    list_cases_view,
    get_case_view,
    delete_case_view,
    list_modules_view,
    validate_proxies_view,
    hudson_check_view,
    scan_stream_view,
    export_csv_view,
    export_json_view,
    export_pdf_view
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def create_app() -> Starlette:
    """Creates and configures the Starlette application."""
    routes = [
        Route("/", endpoint=index_view, methods=["GET"]),
        Route("/api/cases", endpoint=list_cases_view, methods=["GET"]),
        Route("/api/cases/{case_id}", endpoint=get_case_view, methods=["GET"]),
        Route("/api/cases/{case_id}", endpoint=delete_case_view, methods=["DELETE"]),
        Route("/api/modules", endpoint=list_modules_view, methods=["GET"]),
        Route("/api/proxies/validate", endpoint=validate_proxies_view, methods=["POST"]),
        Route("/api/hudson/check", endpoint=hudson_check_view, methods=["GET", "POST"]),
        Route("/api/scan/stream", endpoint=scan_stream_view, methods=["GET", "POST"]),
        Route("/api/export/csv/{case_id}", endpoint=export_csv_view, methods=["GET"]),
        Route("/api/export/json/{case_id}", endpoint=export_json_view, methods=["GET"]),
        Route("/api/export/pdf/{case_id}", endpoint=export_pdf_view, methods=["GET"]),
        Mount("/static", app=StaticFiles(directory=STATIC_DIR), name="static")
    ]
    return Starlette(debug=False, routes=routes)


def start_web_server(host: str = "127.0.0.1", port: int = 8000, target: Optional[str] = None, auto_open: bool = True):
    """Starts the web server with high-visibility terminal banner."""
    app = create_app()

    base_url = f"http://{host}:{port}"
    if target:
        import urllib.parse
        base_url += f"/?u={urllib.parse.quote(target)}"

    print("\033[36m" + "=" * 65 + "\033[0m")
    print("\033[1;32m  USER-SCANNER — OSINT INVESTIGATION WORKBENCH \033[0m")
    print(f"\033[36m  URL: \033[1;37m{base_url}\033[0m")
    print(f"\033[36m  Host: \033[37m{host}  |  Port: \033[37m{port}  |  Engine: \033[35mActive\033[0m")
    print("\033[36m" + "=" * 65 + "\033[0m")
    print("\033[90m  Press CTRL+C in terminal to stop the web server.\033[0m\n")

    if auto_open:
        try:
            webbrowser.open(base_url)
        except Exception:
            pass

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    start_web_server()
