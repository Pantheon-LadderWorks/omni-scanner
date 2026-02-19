"""
Compliance Scanner (Architecture Category)
==========================================
The Enforcer. Checks if components adhere to Federation Standards.

" It's not enough to be a Station; you must also look like one."

Authority:
    - C-HEART-STATION-001 (Station Standards)
    - C-HEART-AGENT-001 (Agent Standards)

Capabilities:
    - Identifies Component Type (Station, Tool, Agent) based on location
    - Checks for Required Files (e.g., station.yaml, README.md)
    - Checks for Forbidden Files (e.g., .env in repo)

Usage:
    omni scan --scanners=architecture.compliance .
"""

import os
from pathlib import Path
from typing import Dict, Any, List

from omni.config import settings
from omni.scanners.architecture.imports import AREA_MAP, _get_sub_area

# Define Standards
STANDARDS = {
    "station": {
        "required": ["station.yaml", "README.md"],
        "recommended": ["src/", "tests/", "Dockerfile"],
        "forbidden": [".env"]
    },
    "agent": {
        "required": ["agent.yaml", "persona.md", "README.md"],
        "recommended": ["memory/", "tools/"],
        "forbidden": [".env", "api_keys.txt"]
    },
    "tool": {
        "required": ["README.md"],
        "recommended": ["pyproject.toml", "package.json", "setup.py"], # At least one
        "forbidden": [".env"]
    },
    "general": {
        "required": [],
        "recommended": ["README.md"],
        "forbidden": [".DS_Store"]
    }
}

def scan(target: Path, **options) -> Dict[str, Any]:
    """
    Scan for Architectural Compliance.
    """
    target = Path(target)
    infra_root = settings.get_infrastructure_root() or target
    
    violations = []
    compliant = []
    
    # Walk the tree, looking for "Roots" of components
    # We use the sub-area logic to find likely component roots
    
    # We can't easily jump to every component without a registry.
    # So we'll scan known top-level directories based on AREA_MAP.
    
    scanned_components = 0
    
    for prefix, area_type in AREA_MAP.items():
        base_dir = infra_root / prefix
        if not base_dir.exists():
            continue
            
        # Iterate immediate children (assuming generic structure like tools/omni, agents/ace)
        # Note: Some prefixes are nested (federation_heart/pillars).
        
        # Special handling for "deep" prefixes
        # If prefix ends in /, it's likely a container.
        
        if not base_dir.is_dir(): continue
        
        for item in base_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                scanned_components += 1
                
                # Determine standard
                std = STANDARDS.get(area_type, STANDARDS["general"])
                
                # Check Requirements
                missing = []
                for req in std["required"]:
                    if not (item / req).exists():
                        missing.append(req)
                        
                # Check Forbidden
                found_forbidden = []
                for forb in std["forbidden"]:
                    if (item / forb).exists():
                        found_forbidden.append(forb)
                        
                # Check Recommended (Partial compliance)
                missing_rec = []
                for rec in std["recommended"]:
                    if not (item / rec).exists():
                        missing_rec.append(rec)
                        
                # Validate "One Of" for tools (package manager)
                if area_type == "tool":
                    has_pkg = any((item / f).exists() for f in ["pyproject.toml", "package.json", "setup.py", "go.mod"])
                    if not has_pkg:
                        missing_rec.append("package_manager_config")

                # Report
                status = "passed"
                if missing or found_forbidden:
                    status = "failed"
                elif missing_rec:
                    status = "warning"
                    
                report = {
                    "component": item.name,
                    "location": str(item.relative_to(infra_root)),
                    "type": area_type,
                    "status": status,
                    "issues": {
                        "missing_required": missing,
                        "found_forbidden": found_forbidden,
                        "missing_recommended": missing_rec
                    }
                }
                
                if status == "passed":
                    compliant.append(report)
                else:
                    violations.append(report)

    return {
        "scanner": "architecture.compliance",
        "components_scanned": scanned_components,
        "summary": {
            "compliant": len(compliant),
            "violating": len(violations),
            "pass_rate": f"{len(compliant) / scanned_components * 100:.1f}%" if scanned_components else "0%"
        },
        "violations": violations
    }
