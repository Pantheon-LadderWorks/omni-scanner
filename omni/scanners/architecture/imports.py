"""
Import Architecture Scanner
============================
AST-based scanner that detects import boundary violations across the Federation.

Contracts define the law. This scanner enforces it.

Modes:
  - heart:    External tools importing federation_heart.clients directly
  - boundary: Cross-area imports (station↔tool, tool↔agent, etc.)
  - all:      Everything

References:
  - C-HEART-CARTOGRAPHY-001 §4-5 (Pillar-first access pattern)
  - C-HEART-CONSTITUTION-001 (Constitution client access via pillar)
  - C-HEART-CONNECTIVITY-001 (Connectivity via pillar)
  - governance/contracts/schemas/SCHEMA_MANIFEST.yaml

Usage via Omni MCP:
  omni_architecture_imports(target="/path/to/Infrastructure")
"""

import ast
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


# ============================================================================
# FEDERATION TOPOLOGY - Where things live and what they're called
# ============================================================================

# Map from directory prefix to architectural area
AREA_MAP = {
    "federation_heart/pillars/": "pillar",
    "federation_heart/clients/": "heart-client",
    "federation_heart/core/": "heart-core",
    "federation_heart/cli/": "heart-cli",
    "federation_heart/scripts/": "heart-scripts",
    "federation_heart/": "heart-internal",
    "tools/": "tool",
    "stations/": "station",
    "agents/": "agent",
    "orchestration/": "orchestration",
    "scripts/": "script",
    "governance/": "governance",
    "protocols/": "protocol",
    "mcp-servers/": "mcp-server",
    "conversation-memory-project/": "cmp",
    "memory-substrate/": "memory",
}

# Which clients map to which pillars
CLIENT_TO_PILLAR = {
    "cartography": ("CartographyPillar", "federation_heart.pillars.cartography"),
    "constitution": ("ConstitutionPillar", "federation_heart.pillars.constitution"),
    "connectivity": ("ConnectivityPillar", "federation_heart.pillars.connectivity"),
    "foundry": ("FoundryPillar", "federation_heart.pillars.foundry"),
    "orchestration": ("OrchestrationPillar", "federation_heart.pillars.orchestration"),
}

# Contract references for violation reports
CONTRACT_REFS = {
    "cartography": "C-HEART-CARTOGRAPHY-001",
    "constitution": "C-HEART-CONSTITUTION-001",
    "connectivity": "C-HEART-CONNECTIVITY-001",
    "foundry": "C-HEART-FOUNDRY-001",
    "orchestration": "C-HEART-ORCHESTRATION-001",
}


# ============================================================================
# AST IMPORT EXTRACTOR
# ============================================================================


from omni.lib.ast_util import extract_imports


# ============================================================================
# AREA CLASSIFICATION
# ============================================================================

def _classify_area(filepath: Path, infra_root: Path) -> str:
    """Determine which architectural area a file belongs to."""
    try:
        rel = filepath.relative_to(infra_root).as_posix()
    except ValueError:
        return "external"

    for prefix, area in AREA_MAP.items():
        if rel.startswith(prefix):
            return area
    return "other"


def _get_sub_area(filepath: Path, infra_root: Path) -> str:
    """Get the specific sub-area (e.g., 'tools/omni' or 'stations/nexus')."""
    try:
        rel = filepath.relative_to(infra_root).as_posix()
    except ValueError:
        return "external"

    parts = rel.split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0] if parts else "unknown"


# ============================================================================
# VIOLATION DETECTION RULES
# ============================================================================

def _check_heart_violation(imp: Dict, caller_area: str, filepath: Path, infra_root: Path) -> Optional[Dict]:
    """
    Rule: External consumers must use pillars, not clients directly.
    
    Contract: C-HEART-*-001 §4-5
    """
    module = imp["module"]

    # Only care about federation_heart.clients imports
    if not module.startswith("federation_heart.clients"):
        return None

    # Pillars importing clients = correct architecture
    if caller_area == "pillar":
        return None

    # Heart-internal clients importing within same package = OK
    if caller_area == "heart-client":
        return None

    # Heart-core and heart-internal get a pass (they're inside the heart)
    if caller_area in ("heart-core",):
        return None

    # Identify which client is being accessed
    parts = module.split(".")
    client_name = parts[2] if len(parts) > 2 else "(barrel)"

    # Build fix suggestion
    pillar_info = CLIENT_TO_PILLAR.get(client_name)
    contract = CONTRACT_REFS.get(client_name, "C-HEART-*-001")

    if pillar_info:
        pillar_class, pillar_module = pillar_info
        fix = f"from {pillar_module} import {pillar_class}"
    else:
        fix = "from federation_heart.pillars.<name> import <PillarName>"

    rel_path = _safe_relative(filepath, infra_root)

    return {
        "file": rel_path,
        "line": imp["line"],
        "import": f"from {module} import {', '.join(imp['names'])}",
        "rule": "heart-pillar-bypass",
        "severity": "error",
        "client": client_name,
        "caller_area": caller_area,
        "fix": fix,
        "contract": contract,
    }


def _check_boundary_violation(imp: Dict, caller_area: str, caller_sub: str,
                               filepath: Path, infra_root: Path) -> Optional[Dict]:
    """
    Rule: Detect cross-boundary imports for visibility.
    
    Not hard-blocked — just reported for awareness. These include:
    - station importing from another station
    - tool importing from another tool 
    - any area importing internals of another area
    """
    module = imp["module"]

    # Check for cross-station imports
    if caller_area == "station" and module.startswith("stations."):
        target_parts = module.split(".")
        caller_parts = caller_sub.split("/")
        if len(target_parts) >= 2 and len(caller_parts) >= 2:
            if target_parts[1] != caller_parts[1]:
                return {
                    "file": _safe_relative(filepath, infra_root),
                    "line": imp["line"],
                    "import": f"from {module} import {', '.join(imp['names'])}",
                    "rule": "cross-station",
                    "severity": "warning",
                    "caller_area": caller_area,
                    "fix": "Consider shared interface or event-based communication",
                    "contract": None,
                }

    return None


def _safe_relative(filepath: Path, infra_root: Path) -> str:
    """Get relative path safely."""
    try:
        return filepath.relative_to(infra_root).as_posix()
    except ValueError:
        return str(filepath)


# ============================================================================
# PATH RESOLUTION — through the pillar pipeline
# ============================================================================

def _resolve_infra_root(target: Path) -> Path:
    """
    Resolve the Infrastructure root using Omni's settings pipeline.
    
    Priority:
      1. Omni settings → CartographyPillar → get_infrastructure_root()
      2. Walk parent directories looking for federation_heart/
      3. Fall back to target itself
    """
    # Try the pillar pipeline first
    try:
        from omni.config.settings import get_infrastructure_root
        resolved = get_infrastructure_root()
        if resolved and resolved.exists():
            return resolved
    except ImportError:
        pass  # Not running inside Omni context

    # Fallback: walk up from target looking for federation_heart/
    if (target / "federation_heart").exists():
        return target
    for parent in target.parents:
        if (parent / "federation_heart").exists():
            return parent

    # Last resort — use target as-is
    return target


# ============================================================================
# MAIN SCANNER
# ============================================================================

def scan(target: Path, **options) -> Dict[str, Any]:
    """
    Scan for import architecture violations.

    Args:
        target: Path to scan (usually Infrastructure root)
        options:
            mode: "heart" | "boundary" | "all" (default: "all")
            include_ok: If True, include compliant imports too (default: False)

    Returns:
        Structured report of violations, grouped by area and rule.
    """
    target = Path(target)

    # Determine Infrastructure root via the pillar pipeline
    infra_root = _resolve_infra_root(target)


    mode = options.get("mode", "all")
    include_ok = options.get("include_ok", False)

    violations = []
    compliant_imports = []
    errors = []
    files_scanned = 0
    
    # Track which files/areas are compliant vs violating
    compliant_files = set()   # Files with correct pillar imports
    violating_files = set()   # Files with client bypass imports

    # Walk all Python files
    skip_dirs = {
        "__pycache__", ".git", "node_modules", ".venv", "venv",
        "archive", ".tox", "build", "dist", ".eggs",
        "external-frameworks",
    }

    for py_file in infra_root.rglob("*.py"):
        # Skip excluded directories
        if any(skip in py_file.parts for skip in skip_dirs):
            continue

        files_scanned += 1
        imports = extract_imports(py_file)
        caller_area = _classify_area(py_file, infra_root)
        caller_sub = _get_sub_area(py_file, infra_root)
        rel_path = _safe_relative(py_file, infra_root)

        for imp in imports:
            # Heart client bypass check
            if mode in ("heart", "all"):
                violation = _check_heart_violation(imp, caller_area, py_file, infra_root)
                if violation:
                    violations.append(violation)
                    violating_files.add(rel_path)
                    continue
                
                # Track correct pillar imports (always, not just include_ok)
                if imp["module"].startswith("federation_heart.pillars"):
                    compliant_files.add(rel_path)
                    if include_ok:
                        compliant_imports.append({
                            "file": rel_path,
                            "line": imp["line"],
                            "import": f"from {imp['module']} import {', '.join(imp['names'])}",
                            "caller_area": caller_area,
                            "sub_area": caller_sub,
                        })

            # Boundary violation check
            if mode in ("boundary", "all"):
                violation = _check_boundary_violation(imp, caller_area, caller_sub, py_file, infra_root)
                if violation:
                    violations.append(violation)

    # ================================================================
    # SETTINGS SHIM AUDIT — check all config/settings.py files
    # ================================================================
    shim_audit = _audit_settings_shims(infra_root, skip_dirs)

    # Group violations by area
    by_area = {}
    for v in violations:
        area = v["caller_area"]
        by_area.setdefault(area, []).append(v)

    # Group violations by rule
    by_rule = {}
    for v in violations:
        rule = v["rule"]
        by_rule.setdefault(rule, []).append(v)

    # Group by client (for heart violations)
    by_client = {}
    for v in violations:
        client = v.get("client", "other")
        by_client.setdefault(client, []).append(v)

    # Group compliant files by sub_area for quick read
    compliant_by_area = {}
    for f in sorted(compliant_files):
        parts = f.split("/")
        area_key = "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        compliant_by_area.setdefault(area_key, []).append(f)

    # Summary
    error_count = sum(1 for v in violations if v["severity"] == "error")
    warning_count = sum(1 for v in violations if v["severity"] == "warning")

    result = {
        "scanner": "architecture.imports",
        "mode": mode,
        "target": str(target),
        "infra_root": str(infra_root),
        "files_scanned": files_scanned,
        "summary": {
            "total_violations": len(violations),
            "errors": error_count,
            "warnings": warning_count,
            "compliant": len(compliant_files),
            "violating": len(violating_files),
        },
        "by_area": {area: len(items) for area, items in sorted(by_area.items())},
        "by_rule": {rule: len(items) for rule, items in sorted(by_rule.items())},
        "by_client": {client: len(items) for client, items in sorted(by_client.items())},
        "compliant_by_area": {area: len(files) for area, files in sorted(compliant_by_area.items())},
        "settings_shim_audit": shim_audit,
        "violations": violations,
    }

    if include_ok:
        result["compliant_files"] = sorted(compliant_files)
        result["compliant_imports"] = compliant_imports

    return result


# ============================================================================
# SETTINGS SHIM AUDIT
# ============================================================================

def _audit_settings_shims(infra_root: Path, skip_dirs: set) -> Dict[str, Any]:
    """
    Audit all config/settings.py files for correct Heart shim pattern.
    
    A correct shim:
      - Imports from federation_heart.pillars.* (NOT federation_heart.clients.*)
      - Uses lazy initialization (get_cartography(), get_constitution(), etc.)
      - Is the ONLY file in its tool/project that touches federation_heart
    
    Returns a per-file audit with status: clean, broken, or no-shim.
    """
    shims = []
    
    # Find all settings.py files that follow the config/settings.py pattern
    for settings_file in infra_root.rglob("config/settings.py"):
        if any(skip in settings_file.parts for skip in skip_dirs):
            continue
        
        rel_path = _safe_relative(settings_file, infra_root)
        
        # Skip federation_heart's own settings (not a shim)
        if rel_path.startswith("federation_heart/"):
            continue
        
        imports = extract_imports(settings_file)
        
        pillar_imports = [i for i in imports 
                         if i["module"].startswith("federation_heart.pillars")]
        client_imports = [i for i in imports 
                         if i["module"].startswith("federation_heart.clients")]
        
        if pillar_imports and not client_imports:
            status = "clean"
        elif client_imports:
            status = "broken"
        elif not pillar_imports and not client_imports:
            status = "no-shim"
        else:
            status = "clean"
        
        shims.append({
            "file": rel_path,
            "status": status,
            "pillar_imports": len(pillar_imports),
            "client_imports": len(client_imports),
            "client_details": [
                {"line": i["line"], "module": i["module"]} 
                for i in client_imports
            ],
        })
    
    clean = sum(1 for s in shims if s["status"] == "clean")
    broken = sum(1 for s in shims if s["status"] == "broken")
    no_shim = sum(1 for s in shims if s["status"] == "no-shim")
    
    return {
        "total": len(shims),
        "clean": clean,
        "broken": broken,
        "no_shim": no_shim,
        "shims": shims,
    }

