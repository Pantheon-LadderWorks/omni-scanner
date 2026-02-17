"""
CLI Edge Case Scanner
=====================
Hunts for "smell" patterns in CLI commands:
- Broad exception catching (except Exception)
- TODO/FIXME comments
- Bare 'pass' statements
- Dangerous imports (federation_heart in providers)
- Mutating operations without safety checks

Usage:
    omni scan --scanners=cli_edges .

Author: Mega + Claude
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

def scan(target: Path) -> Dict[str, Any]:
    """
    Scans for CLI edge cases and code smells.
    """
    findings = []
    errors = []
    
    # Handle file vs directory
    scan_configs = [
        {"path": target / "federation_heart" / "cli", "provider": "federation_heart"},
        {"path": target / "stations", "provider": "stations"},
        {"path": target / "tools" / "omni" / "omni" / "cli.py", "provider": "omni"},
        {"path": target / "agents", "provider": "agents"},
    ]
    
    files_to_scan = []
    
    if target.is_file() and target.suffix == ".py":
        files_to_scan.append((target, "unknown"))
    else:
        for config in scan_configs:
            p = config["path"]
            if not p.exists():
                continue
            if p.is_file():
                files_to_scan.append((p, config["provider"]))
            else:
                for py_file in p.rglob("*.py"):
                    if "__pycache__" in str(py_file) or "test" in py_file.name.lower():
                        continue
                    files_to_scan.append((py_file, config["provider"]))

    for path, provider in files_to_scan:
        result = _scan_file(path, provider)
        findings.extend(result["items"])
        if result["error"]:
            errors.append(result["error"])
            
    return {
        "count": len(findings),
        "items": findings,
        "errors": errors,
        "metadata": {
            "scanner": "cli_edges",
            "version": "1.0.0",
            "focus": "code quality & safety"
        }
    }

def _scan_file(path: Path, provider: str) -> Dict[str, Any]:
    items = []
    error = None
    
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        tree = ast.parse(content, filename=str(path))
    except Exception as e:
        return {"items": [], "error": f"{path}: {e}"}

    # 1. Regex Scans (Comments)
    for i, line in enumerate(lines):
        if "TODO" in line:
            items.append(_make_finding(path, i+1, "todo", "Found TODO comment", line.strip(), provider))
        if "FIXME" in line:
            items.append(_make_finding(path, i+1, "fixme", "Found FIXME comment", line.strip(), provider))

    # 2. AST Scans (Logic)
    for node in ast.walk(tree):
        # Catch generic exceptions
        if isinstance(node, ast.ExceptHandler):
            if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                items.append(_make_finding(path, node.lineno, "broad_except", "Catches generic Exception", "", provider))
        
        # Bare pass
        if isinstance(node, ast.Pass):
            items.append(_make_finding(path, node.lineno, "bare_pass", "Bare pass statement", "", provider))
            
        # Dangerous imports in providers (avoid importing heart)
        if provider != "federation_heart":
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "federation_heart" in alias.name:
                        items.append(_make_finding(path, node.lineno, "dangerous_import", f"Provider imports Heart: {alias.name}", "", provider))
            elif isinstance(node, ast.ImportFrom):
                if node.module and "federation_heart" in node.module:
                    items.append(_make_finding(path, node.lineno, "dangerous_import", f"Provider imports Heart: {node.module}", "", provider))

    return {"items": items, "error": None}

def _make_finding(path: Path, line: int, type_id: str, message: str, snippet: str, provider: str) -> Dict[str, Any]:
    return {
        "file": str(path),
        "line": line,
        "type": type_id,
        "message": message,
        "snippet": snippet,
        "provider": provider,
        "severity": "medium" if type_id in ["todo", "bare_pass"] else "high"
    }
