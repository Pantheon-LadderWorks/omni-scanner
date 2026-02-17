"""
📦 Package Scanner - Python Package Detection

Detects pip packages (pyproject.toml, setup.py) and analyzes metadata.
Part of Omni v0.6.0 polyglot scanner suite.

Author: Oracle + Federation Integration
Version: 1.0.0
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def scan(target: Path) -> Dict[str, Any]:
    """
    Scan for Python packages (pip-installable components).
    
    Detects:
    - pyproject.toml (modern standard)
    - setup.py (legacy)
    - Package metadata (name, version, entry points)
    - Triple interface pattern (CLI, MCP, HTTP)
    
    Returns:
        {
            "count": int,
            "items": [package_metadata],
            "summary": {
                "total": int,
                "with_cli": int,
                "with_mcp": int,
                "with_http": int,
                "triple_interface": int
            }
        }
    """
    target_path = Path(target).resolve()
    root = target_path if target_path.is_dir() else target_path.parent
    
    packages = []
    
    # Walk and find package markers
    for item in root.rglob("*"):
        if item.name in ["pyproject.toml", "setup.py"]:
            pkg_info = _extract_package_info(item)
            if pkg_info:
                packages.append(pkg_info)
    
    # Summary statistics
    summary = {
        "total": len(packages),
        "with_cli": sum(1 for p in packages if p.get("entry_points", {}).get("cli")),
        "with_mcp": sum(1 for p in packages if p.get("entry_points", {}).get("mcp")),
        "with_http": sum(1 for p in packages if p.get("entry_points", {}).get("http")),
        "triple_interface": sum(1 for p in packages if _has_triple_interface(p))
    }
    
    return {
        "count": len(packages),
        "items": packages,
        "summary": summary
    }


def _extract_package_info(package_file: Path) -> Dict[str, Any]:
    """Extract package metadata from pyproject.toml or setup.py."""
    pkg_root = package_file.parent
    pkg_name = pkg_root.name
    
    info = {
        "name": pkg_name,
        "path": str(pkg_root),
        "manifest": package_file.name,
        "entry_points": {}
    }
    
    if package_file.name == "pyproject.toml":
        info.update(_parse_pyproject_toml(package_file))
    elif package_file.name == "setup.py":
        info.update(_parse_setup_py(package_file))
    
    # Detect triple interface pattern
    _detect_interfaces(pkg_root, info)
    
    return info


def _parse_pyproject_toml(file_path: Path) -> Dict[str, Any]:
    """Parse pyproject.toml for package metadata."""
    try:
        import tomli
    except ImportError:
        # Fallback: manual parsing (limited)
        return _parse_pyproject_manual(file_path)
    
    with open(file_path, "rb") as f:
        data = tomli.load(f)
    
    project = data.get("project", {})
    return {
        "version": project.get("version", "unknown"),
        "description": project.get("description", ""),
        "cli_scripts": project.get("scripts", {})
    }


def _parse_pyproject_manual(file_path: Path) -> Dict[str, Any]:
    """Manual TOML parsing (basic, no dependencies)."""
    info = {"version": "unknown", "description": "", "cli_scripts": {}}
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    in_project = False
    in_scripts = False
    
    for line in lines:
        line = line.strip()
        
        if line == "[project]":
            in_project = True
            in_scripts = False
        elif line == "[project.scripts]":
            in_scripts = True
            in_project = False
        elif line.startswith("["):
            in_project = False
            in_scripts = False
        
        if in_project and "version" in line and "=" in line:
            version_str = line.split("=", 1)[1].strip().strip('"\'')
            info["version"] = version_str
        
        if in_scripts and "=" in line and not line.startswith("#"):
            name, entry = line.split("=", 1)
            info["cli_scripts"][name.strip()] = entry.strip().strip('"\'')
    
    return info


def _parse_setup_py(file_path: Path) -> Dict[str, Any]:
    """Parse setup.py for package metadata (basic extraction)."""
    info = {"version": "unknown", "description": "", "cli_scripts": {}}
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Extract version (simple regex)
    import re
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        info["version"] = version_match.group(1)
    
    return info


def _detect_interfaces(pkg_root: Path, info: Dict[str, Any]) -> None:
    """Detect CLI, MCP, HTTP entry points."""
    
    # CLI: Check cli_scripts or __main__.py
    if info.get("cli_scripts"):
        info["entry_points"]["cli"] = list(info["cli_scripts"].keys())
    elif (pkg_root / "__main__.py").exists():
        info["entry_points"]["cli"] = [f"python -m {pkg_root.name}"]
    
    # MCP: Check for mcp_server.py or *_mcp_server.py
    mcp_files = list(pkg_root.glob("*mcp_server.py")) + list(pkg_root.glob("**/mcp_server.py"))
    if mcp_files:
        info["entry_points"]["mcp"] = [f.stem for f in mcp_files[:3]]  # Limit to 3
    
    # HTTP: Check for server.py, api.py, app.py
    http_patterns = ["server.py", "api.py", "app.py", "api_server.py"]
    http_files = []
    for pattern in http_patterns:
        http_files.extend(pkg_root.glob(f"**/{pattern}"))
    if http_files:
        info["entry_points"]["http"] = [f.stem for f in http_files[:3]]  # Limit to 3


def _has_triple_interface(pkg_info: Dict[str, Any]) -> bool:
    """Check if package has all three interfaces (CLI, MCP, HTTP)."""
    entry_points = pkg_info.get("entry_points", {})
    return bool(
        entry_points.get("cli") and
        entry_points.get("mcp") and
        entry_points.get("http")
    )
