"""
omni/config/settings_template.py

CONFIGURATION TEMPLATE
======================
HOW TO USE:
1. Rename this file to 'settings.py'
2. Setup your configuration:
   a) Environment Variables (OMNI_ROOT, etc.)
   b) OR create 'omni_config.yaml' in your infrastructure root
3. Do NOT commit your 'settings.py' if it contains sensitive paths.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Optional

# Setup Logging
logger = logging.getLogger("Omni.Config")

# =============================================================================
# 🌍 INFRASTRUCTURE ROOTS
# =============================================================================

# 1. Determine Root Pth
# Fallback: We assume "tools/omni/omni/config" depth (4 levels up)
_DEFAULT_FALLBACK = Path(__file__).resolve().parents[4]
INFRA_ROOT = Path(os.getenv("OMNI_ROOT", _DEFAULT_FALLBACK))

# 2. Load YAML Config (if exists)
_CONFIG = {}
_config_path = INFRA_ROOT / "omni_config.yaml"
if _config_path.exists():
    try:
        with open(_config_path, "r") as f:
            _CONFIG = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load omni_config.yaml: {e}")

# =============================================================================
# 📍 PATH RESOLUTION
# =============================================================================

def get_infrastructure_root() -> Path:
    """Get the root directory for scanning."""
    # YAML override?
    if "infrastructure_root" in _CONFIG:
        return Path(_CONFIG["infrastructure_root"])
    return INFRA_ROOT

def get_repo_inventory_path() -> Path:
    """Path to repo_inventory.json."""
    if "repo_inventory" in _CONFIG:
        return Path(_CONFIG["repo_inventory"])
    
    env_path = os.getenv("OMNI_REPO_INVENTORY")
    if env_path:
        return Path(env_path)
        
    return get_infrastructure_root() / "omni_repos.json"

def get_project_registry_path() -> Path:
    """Path to projects.yaml."""
    if "project_registry" in _CONFIG:
        return Path(_CONFIG["project_registry"])
    return get_infrastructure_root() / "projects.yaml"

def get_all_workspaces() -> list:
    """Get list of workspace roots."""
    if "workspaces" in _CONFIG:
        return [Path(p) for p in _CONFIG["workspaces"]]
    return [get_infrastructure_root()]

def get_council_members() -> list:
    """Get list of council members for PR telemetry."""
    return _CONFIG.get("council_members", ["owner", "admin", "bot"])

def get_contract_map() -> dict:
    """Get contract family definitions for Surfaces scanner."""
    return _CONFIG.get("contracts", {
        "mcp": {"ref": "contracts/mcp.md", "status": "partial"},
        "http": {"ref": "contracts/api.md", "status": "partial"},
        "cli": {"ref": "contracts/cli.md", "status": "partial"},
        "bus_topic": {"ref": "contracts/bus.md", "status": "partial"},
        "db": {"ref": "contracts/db.md", "status": "partial"},
        "doc": {"ref": "contracts/doc.md", "status": "partial"},
        "ui_integration": {"ref": "contracts/ui.md", "status": "partial"}
    })
    
def get_git_config() -> dict:
    """
    Get Git scanner configuration.
    Returns dict with keys:
    - github_enabled: bool
    - users: List[str] (GitHub users to scan)
    - orgs: List[str] (GitHub orgs to scan)
    - registry_enabled: bool (Maintain specific repo_inventory.json)
    """
    git_conf = _CONFIG.get("git", {})
    return {
        "github_enabled": git_conf.get("github_enabled", False),
        "users": git_conf.get("users", []),
        "orgs": git_conf.get("orgs", []),
        "registry_enabled": git_conf.get("registry_enabled", False),
        "auto_update": git_conf.get("auto_update", False)
    }

def get_omni_artifacts_path() -> Path:
    """Where to save Omni reports."""
    # 1. Env Override (Sandbox/CI)
    env_path = os.getenv("OMNI_ARTIFACTS")
    if env_path:
        return Path(env_path)
        
    # 2. Config Override
    if "artifacts" in _CONFIG:
        return Path(_CONFIG["artifacts"])
        
    # 3. Default (In-tree)
    return get_infrastructure_root() / "tools/omni/artifacts/omni"

# =============================================================================
# 🔌 STUB ACCESSORS (For Compatibility)
# =============================================================================
# These stubs ensure code expecting the Federation Heart structure still runs
# (albeit with limited functionality) in standalone mode.

def get_core(): return None
def get_constitution(): return None
def get_cartography(): return None
def get_connectivity(): return None
def get_foundry(): return None
def get_consciousness(): return None

# Module-level shortcuts
def __getattr__(name: str):
    if name in ["constitution", "cartography", "connectivity", 
                "foundry", "consciousness", "core"]:
        return None
    elif name == "heart_available":
        return False
    raise AttributeError(f"module 'settings' has no attribute '{name}'")

def status() -> dict:
    return {
        "mode": "Standalone (Template)",
        "infra_root": str(get_infrastructure_root()),
        "config_file": str(_config_path) if _config_path.exists() else None
    }

def get_database_config_path():
    """
    Get path to database configuration directory.
    Priority:
    1. Env: OMNI_DB_CONFIG_PATH
    2. Local: omni/config/db
    3. Global: Infrastructure/config/omni/db
    """
    env_path = os.environ.get("OMNI_DB_CONFIG_PATH")
    if env_path:
        return Path(env_path)
        
    local_path = Path.cwd() / "omni" / "config" / "db"
    if local_path.exists():
        return local_path
        
    infra = get_infrastructure_root()
    if infra:
        global_path = infra / "config" / "omni" / "db"
        if global_path.exists():
            return global_path
            
    return None
