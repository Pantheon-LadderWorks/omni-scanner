"""
omni/config/settings.py

Federation Heart Wiring Shim for Omni
=====================================
This is the ONLY file in Omni that imports from federation_heart.
All other modules should import from here to get Heart connectivity.

Pattern (matches scheduling subsystem):
    from omni.config.settings import constitution, cartography, connectivity
    
    # Use pillar methods
    infra_root = cartography.get_infrastructure_root()

Environment Variables (Standalone Mode):
    OMNI_ROOT: Override the infrastructure root path.
    OMNI_REPO_INVENTORY: Override path to repo_inventory.json.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# 1. Load Environment Variables (The Cloud Native Way)
from dotenv import load_dotenv
load_dotenv() 

logger = logging.getLogger("Omni.Config")

# =============================================================================
# 🌍 UNIVERSAL PATHS (The Fallback)
# =============================================================================
# If OMNI_ROOT isn't set, assume we are running relative to this file
# Repo structure: tools/omni/omni/config/settings.py
# Fallback root (if this file is in tools/omni/omni/config)
# We assume the "Infrastructure" root is 4 levels up from here.
_DEFAULT_FALLBACK = Path(__file__).resolve().parents[4]
INFRA_ROOT = Path(os.getenv("OMNI_ROOT", _DEFAULT_FALLBACK))

# =============================================================================
# ❤️ FEDERATION HEART (The Pantheon Connection)
# =============================================================================

# =============================================================================
# ❤️ FEDERATION HEART (The Pantheon Connection)
# =============================================================================

_core = None
_constitution = None
_cartography = None
_connectivity = None
_foundry = None
_consciousness = None
_heart_available = None

def _check_heart_available() -> bool:
    """Check if we are running inside The Pantheon (Kryssie's rig)."""
    global _heart_available
    if _heart_available is None:
        try:
            import federation_heart  # noqa
            _heart_available = True
        except ImportError:
            _heart_available = False
    return _heart_available

def get_infrastructure_root() -> Path:
    """
    The Master Logic:
    1. Ask the Heart (if connected).
    2. Ask the Environment Variable (OMNI_ROOT).
    3. Fallback to Relative Path.
    """
    # 1. Try Heart
    if _check_heart_available():
        try:
            from federation_heart.pillars import cartography
            return cartography.get_infrastructure_root()
        except Exception:
            pass # Heart broken? Fallthrough.
            
    # 2. Return Env/Default
    return INFRA_ROOT

# =============================================================================
# 🔌 EXPORTS (The Public API)
# =============================================================================

def get_repo_inventory_path() -> Path:
    # Public users: Look for a simple 'repos.json' in their root
    # You: Look in governance/registry...
    root = get_infrastructure_root()
    if _check_heart_available():
        try:
            from federation_heart.pillars import cartography
            # Note: Cartography might have a direct method, but resolving path is safer
            return cartography.resolve_path("governance") / "registry/git_repos/repo_inventory.json"
        except Exception:
            pass
            
    # Fallback/Standalone
    env_path = os.getenv("OMNI_REPO_INVENTORY")
    if env_path:
        return Path(env_path)
    return root / "omni_repos.json"

def get_project_registry_path() -> Path:
    root = get_infrastructure_root()
    if _check_heart_available():
        try:
            from federation_heart.pillars import cartography
            return cartography.resolve_path("governance") / "registry/projects/PROJECT_REGISTRY_V1.yaml"
        except Exception:
            pass
    return root / "projects.yaml"

def get_all_workspaces() -> list:
    """Get all workspace root paths."""
    if _check_heart_available():
        try:
            from federation_heart.pillars import cartography
            return cartography.get_all_workspaces()
        except Exception:
            pass
    
    # Fallback: check env var OMNI_WORKSPACES (comma separated)
    env_ws = os.getenv("OMNI_WORKSPACES")
    if env_ws:
        return [Path(p.strip()) for p in env_ws.split(",")]
        
    return [get_infrastructure_root()]

def get_council_members() -> list:
    """Get list of council members for PR telemetry."""
    # Future: Could query Heart/Constitution
    return ["kryst", "ace", "mega", "oracle", "renovate", "dependabot", "app/renovate", "app/dependabot"]

def get_contract_map() -> dict:
    """Get contract family definitions for Surfaces scanner."""
    # Pantheon Defaults
    start_path = get_infrastructure_root() / "governance/contracts"
    return {
        "mcp": {
            "ref": str(start_path / "mcp/C-MCP-BASE-001.md"),
            "status": "partial" 
        },
        "http": {
            "ref": str(start_path / "http/C-HTTP-BASE-001.md"),
            "status": "partial" 
        },
        "cli": {
            "ref": str(start_path / "cli/C-CLI-BASE-001.md"),
            "status": "partial"
        },
        "bus_topic": {
            "ref": str(start_path / "system/C-SYS-BUS-001_Quadruplet_Crown_Bus.md"),
            "status": "partial"
        },
        "db": {
            "ref": str(start_path / "db/C-DB-BASE-001.md"),
            "status": "partial"
        },
        "doc": { 
            "ref": str(start_path / "artifacts/C-ARTIFACT-BASE-001.md"),
            "status": "partial"
        },
        "ui_integration": {
            "ref": str(start_path / "ui/C-UI-BASE-001.md"),
            "status": "partial"
        }
    }

def get_omni_artifacts_path() -> Path:
    """Omni artifacts output directory."""
    # Defaut: tools/omni/artifacts/omni relative to infra root
    return get_infrastructure_root() / "tools/omni/artifacts/omni"

def get_git_config() -> dict:
    """
    Get Git scanner configuration.
    """
    # 1. Heart (The User's Rig)
    if _check_heart_available():
        # The user always wants their rig to have full power
        return {
            "github_enabled": True,
            "users": [], # Auto-detect current user
            "orgs": [],  # Auto-detect user orgs
            "registry_enabled": True, 
            "auto_update": True
        }
        
    # 2. Env/YAML (Skeleton Key for Standalone)
    # We should really add YAML loading here too, but for now Env is the shim
    return {
        "github_enabled": os.getenv("OMNI_GIT_GITHUB", "False").lower() == "true",
        "users": [],
        "orgs": [],
        "registry_enabled": False,
        "auto_update": False
    }

# =============================================================================
# 🔮 PILLAR & CORE ACCESSORS (The Gateway)
# =============================================================================

def get_core():
    global _core
    if _core is None and _check_heart_available():
        try:
            from federation_heart.core.federation_core import FederationCore
            _core = FederationCore()
        except Exception:
            pass
    return _core

def get_constitution():
    global _constitution
    if _constitution is None and _check_heart_available():
        try:
            from federation_heart.pillars.constitution import ConstitutionPillar
            from federation_heart.pillars import cartography
            
            # This is a bit recursive if constitution needs cartography, but standard pattern
            infra_root = cartography.get_infrastructure_root()
            _constitution = ConstitutionPillar(infra_root)
        except Exception:
            pass
    return _constitution

def get_cartography():
    global _cartography
    if _cartography is None and _check_heart_available():
        try:
            from federation_heart.pillars.cartography import CartographyPillar
            _cartography = CartographyPillar()
        except Exception:
            pass
    return _cartography

def get_connectivity():
    global _connectivity
    if _connectivity is None and _check_heart_available():
        try:
            from federation_heart.pillars.connectivity import ConnectivityPillar
            _connectivity = ConnectivityPillar()
        except Exception:
            pass
    return _connectivity

def get_foundry():
    global _foundry
    if _foundry is None and _check_heart_available():
        try:
            from federation_heart.pillars.foundry import FoundryPillar
            _foundry = FoundryPillar()
        except Exception:
            pass
    return _foundry

def get_consciousness():
    global _consciousness
    if _consciousness is None and _check_heart_available():
        try:
            from federation_heart.pillars.consciousness import ConsciousnessPillar
            _consciousness = ConsciousnessPillar()
        except Exception:
            pass
    return _consciousness

# Module-level shortcuts
def __getattr__(name: str):
    if name == "constitution": return get_constitution()
    elif name == "cartography": return get_cartography()
    elif name == "connectivity": return get_connectivity()
    elif name == "foundry": return get_foundry()
    elif name == "consciousness": return get_consciousness()
    elif name == "core": return get_core()
    elif name == "heart_available": return _check_heart_available()
    raise AttributeError(f"module 'settings' has no attribute '{name}'")

def status() -> dict:
    return {
        "heart_available": _check_heart_available(),
        "infra_root": str(get_infrastructure_root()),
        "mode": "Pantheon" if _check_heart_available() else "Standalone"
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
