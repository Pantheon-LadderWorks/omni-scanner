from pathlib import Path

def create_contract(target: Path, force: bool = False):
    file_path = target / "CONTRACT.md"
    if file_path.exists() and not force:
        print(f"⚠️ {file_path} already exists. Use --force to overwrite.")
        return

    content = """# Contract

**ID**: C-XXX-YYY-001
**Status**: DRAFT
**Owner**: owner@federation.net

## 1. Overview
Describe the purpose of this component.

## 2. API
Describe the API surface.
"""
    file_path.write_text(content, encoding="utf-8")
    print(f"[OK] Created {file_path}")

def create_openapi_script(target: Path, force: bool = False):
    file_path = target / "dump_openapi.py"
    if file_path.exists() and not force:
        print(f"⚠️ {file_path} already exists. Use --force to overwrite.")
        return

    content = """import json
from fastapi.openapi.utils import get_openapi
# from myapp import app (ADJUST THIS IMPORT)

def main():
    # spec = get_openapi(title="My API", version="1.0.0", routes=app.routes)
    # print(json.dumps(spec, indent=2))
    print("Please configure the 'app' import in this script first.")

if __name__ == "__main__":
    main()
"""
    file_path.write_text(content, encoding="utf-8")
    print(f"[OK] Created {file_path}")
