"""
Artifacts Library
=================
Central logic for naming, locating, and managing Omni scan artifacts.

Standard:
    scan.<scanner>.<scope>.json

Usage:
    from omni.lib import artifacts
    
    path = artifacts.get_scan_path(scanner="drift", scope="global")
    # -> .../tools/omni/artifacts/omni/scan.drift.global.json
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from omni.config import settings

def get_artifacts_root() -> Path:
    """Get the root directory for Omni artifacts."""
    # Use settings if available, else fallback
    if hasattr(settings, 'get_omni_artifacts_path'):
        return settings.get_omni_artifacts_path()
    
    # Fallback mostly for standalone/testing without full settings
    try:
        root = settings.get_infrastructure_root()
        return root / "tools/omni/artifacts/omni"
    except Exception:
        return Path("artifacts/omni")

def get_scan_path(scanner: str, scope: str = "default", extension: str = "json") -> Path:
    """
    Generate the standard path for a scan artifact.
    
    Args:
        scanner: Name of the scanner (e.g., 'drift', 'surfaces', 'all')
        scope: Target scope slug (e.g., 'global', 'infrastructure', 'my_project')
        extension: File extension (default: 'json')
        
    Returns:
        Path object for the artifact.
    """
    root = get_artifacts_root()
    root.mkdir(parents=True, exist_ok=True)
    
    # Clean inputs
    scanner = scanner.lower().strip()
    scope = scope.lower().strip().replace(os.sep, "_").replace(":", "_")
    
    filename = f"scan.{scanner}.{scope}.{extension}"
    return root / filename

def get_latest_scan(scanner: str, scope: str = "*") -> Optional[Path]:
    """Find the most recent scan for a given scanner."""
    root = get_artifacts_root()
    if not root.exists():
        return None
        
    pattern = f"scan.{scanner}.{scope}.json"
    matches = list(root.glob(pattern))
    
    if not matches:
        return None
        
    # Python 3.10+ windows mtime logic is usually fine
    return max(matches, key=os.path.getmtime)
