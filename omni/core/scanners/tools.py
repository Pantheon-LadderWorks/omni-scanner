from pathlib import Path
import re

def scan(target: Path) -> dict:
    """
    Scans for installable CLI tools (entry points).
    """
    found_tools = []
    
    # 1. Check pyproject.toml (Standard Python)
    pyproject = target / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            # Simple regex search for [project.scripts] section
            # We could parse toml, but want to keep deps low/zero if possible
            # or use simple parsing if we imported toml lib (we didn't yet)
            
            # Using basic string check for robustness without 'tomli' dep
            if "[project.scripts]" in content or "[tool.poetry.scripts]" in content:
                 # Try to extract the names
                 lines = content.splitlines()
                 in_scripts = False
                 for line in lines:
                     if line.strip().startswith("[project.scripts]") or line.strip().startswith("[tool.poetry.scripts]"):
                         in_scripts = True
                         continue
                     if line.strip().startswith("[") and in_scripts: 
                         in_scripts = False # Next section
                     
                     if in_scripts and "=" in line:
                         tool_name = line.split("=")[0].strip()
                         if tool_name:
                             found_tools.append(f"{tool_name} (local-py)")
        except Exception:
            pass

    # 2. Check package.json (Node)
    pkg_json = target / "package.json"
    if pkg_json.exists():
        try:
             content = pkg_json.read_text(encoding="utf-8")
             if '"bin":' in content:
                 found_tools.append("node-bin (npm)")
        except Exception:
            pass
            
    # 3. Check setup.py (Legacy Python)
    setup_py = target / "setup.py"
    if setup_py.exists():
        try:
            content = setup_py.read_text(encoding="utf-8")
            if "entry_points" in content or "console_scripts" in content:
                found_tools.append("setup-script (legacy-py)")
        except Exception:
            pass

    return {
        "count": len(found_tools),
        "items": found_tools
    }
