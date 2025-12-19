import json
import httpx
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VERSION_FILE = SCRIPT_DIR.parent / "version.json"


def load_local_version():
    try:
        data = json.loads(VERSION_FILE.read_text())
        return data.get("version", "error_report_via_gh_issues"), data.get("version_type", "local")
    except FileNotFoundError:
        return "N/A", "file_missing"
    except json.JSONDecodeError:
        return "N/A", "json_error"
    except Exception:
        return "N/A", "error"


def get_pypi_version(pypi_url):
    try:
        pypi_version = httpx.get(pypi_url, timeout=7).json()["info"]["version"]
    except Exception as e:
        print(e)
        return None
    return pypi_version

if __name__ == "__main__":
    version, version_type = load_local_version()
    print(f"Version: {version}, Type: {version_type}")
