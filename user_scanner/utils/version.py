import json
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
VERSION_FILE = _SCRIPT_DIR.parent / "version.json"

def load_local_version():
    try:
        data = json.loads(VERSION_FILE.read_text())
        return data.get("version", "0.0.0"), data.get("version_type", "local")
    except FileNotFoundError:
        return "N/A", "file_missing"
    except json.JSONDecodeError:
        return "N/A", "json_error"
    except Exception:
        return "N/A", "error"

if __name__ == "__main__":
    version, version_type = load_local_version()
    print(f"Version: {version}, Type: {version_type}")
