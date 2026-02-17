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
    gov_path = cartography.resolve_path("governance")
    
    # Connectivity (stations, tunnels)
    connectivity.list_tunnels()
    connectivity.route_to_station(station_id, action, payload)
    
    # Helpers (wrap paths.py through pillar-first access)
    from omni.config.settings import get_all_workspaces, get_languages_path
"""

import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("Omni.Config")

# =============================================================================
# Federation Heart Connection (Lazy Initialization)
# =============================================================================

_constitution = None
_cartography = None
_connectivity = None
_heart_available = None


def _check_heart_available() -> bool:
    """Check if Federation Heart is importable."""
    global _heart_available
    if _heart_available is None:
        try:
            from federation_heart.pillars import constitution  # noqa: F401
            _heart_available = True
        except ImportError:
            _heart_available = False
            logger.warning("⚠️ Federation Heart not available - running in standalone mode")
    return _heart_available


def get_constitution():
    """Get the Constitution Pillar instance (lazy load)."""
    global _constitution
    if _constitution is None and _check_heart_available():
        try:
            from federation_heart.pillars.constitution import ConstitutionPillar
            
            carto = get_cartography()
            infra_root = carto.get_infrastructure_root() if carto else _FALLBACK_INFRA_ROOT
            
            _constitution = ConstitutionPillar(infra_root, cartography=carto)
            logger.info("📜 Constitution Pillar connected")
        except Exception as e:
            logger.error(f"Failed to initialize Constitution Pillar: {e}")
    return _constitution


def get_cartography():
    """Get the Cartography Pillar instance (lazy load)."""
    global _cartography
    if _cartography is None and _check_heart_available():
        try:
            from federation_heart.pillars.cartography import CartographyPillar
            _cartography = CartographyPillar()
            logger.info("🗺️ Cartography Pillar connected")
        except Exception as e:
            logger.error(f"Failed to initialize Cartography Pillar: {e}")
    return _cartography


def get_connectivity():
    """Get the Connectivity Pillar instance (lazy load)."""
    global _connectivity
    if _connectivity is None and _check_heart_available():
        try:
            from federation_heart.pillars.connectivity import ConnectivityPillar
            _connectivity = ConnectivityPillar()
            logger.info("🔌 Connectivity Pillar connected")
        except Exception as e:
            logger.error(f"Failed to initialize Connectivity Pillar: {e}")
    return _connectivity


# =============================================================================
# Module-Level Lazy Properties
# =============================================================================
# These allow: `from omni.config.settings import constitution, cartography`

def __getattr__(name: str):
    """Module-level lazy attribute access."""
    if name == "constitution":
        return get_constitution()
    elif name == "cartography":
        return get_cartography()
    elif name == "connectivity":
        return get_connectivity()
    elif name == "heart_available":
        return _check_heart_available()
    raise AttributeError(f"module 'settings' has no attribute '{name}'")


# =============================================================================
# Path Resolution Helpers (Fallbacks for standalone mode)
# =============================================================================

# Hardcoded fallbacks when Federation Heart is unavailable
_FALLBACK_INFRA_ROOT = Path(r"C:\Users\kryst\Infrastructure")


def get_infrastructure_root() -> Path:
    """Get Infrastructure root path."""
    carto = get_cartography()
    if carto:
        try:
            return carto.get_infrastructure_root()
        except Exception:
            pass
    return _FALLBACK_INFRA_ROOT


def get_governance_path(subpath: str = "") -> Path:
    """Get governance/ path, optionally with subpath."""
    carto = get_cartography()
    if carto:
        try:
            gov = carto.resolve_path("governance")
            return gov / subpath if subpath else gov
        except Exception:
            pass
    base = _FALLBACK_INFRA_ROOT / "governance"
    return base / subpath if subpath else base


def get_repo_inventory_path() -> Path:
    """Get path to repo_inventory.json."""
    return get_governance_path("registry/git_repos/repo_inventory.json")


def get_cmp_registry_path() -> Path:
    """Get path to CMP project registry."""
    return _FALLBACK_INFRA_ROOT / "conversation-memory-project" / "PANTHEON_PROJECT_REGISTRY.final.yaml"


def get_master_registry_path() -> Path:
    """Get path to master entity registry."""
    return get_governance_path("registry/infrastructure/PROJECT_REGISTRY_MASTER.md")


def get_identity_namespace_path() -> Path:
    """Get path to IDENTITY_NAMESPACE.yaml."""
    return get_governance_path("registry/projects/IDENTITY_NAMESPACE.yaml")


def get_registry_overrides_path() -> Path:
    """Get path to LOCAL_OVERRIDES_V1.yaml."""
    return get_governance_path("registry/projects/LOCAL_OVERRIDES_V1.yaml")


def get_project_registry_path() -> Path:
    """Get path to canonical PROJECT_REGISTRY_V1.yaml."""
    return get_governance_path("registry/projects/PROJECT_REGISTRY_V1.yaml")



def get_all_workspaces() -> list:
    """Get all workspace root paths (Infrastructure, Workspace, Deployment, etc.)."""
    carto = get_cartography()
    if carto:
        try:
            return carto.get_all_workspaces()
        except Exception:
            pass
    return [_FALLBACK_INFRA_ROOT]


def get_languages_path() -> Path:
    """Get path to languages/ directory."""
    carto = get_cartography()
    if carto:
        try:
            return carto.resolve_path("languages")
        except Exception:
            pass
    return _FALLBACK_INFRA_ROOT / "languages"


def load_project_registry() -> dict:
    """Load PROJECT_REGISTRY_V1.yaml via CartographyPillar's RegistryClient."""
    carto = get_cartography()
    if carto:
        try:
            registry = carto.get_registry("projects")
            return registry or {}
        except Exception:
            pass
    return {}


def get_omni_artifacts_path() -> Path:
    """Get path to Omni artifacts output directory."""
    return _FALLBACK_INFRA_ROOT / "tools/omni/omni/artifacts/omni"


# =============================================================================
# Status Check
# =============================================================================

def status() -> dict:
    """Get Heart connection status."""
    return {
        "heart_available": _check_heart_available(),
        "constitution": get_constitution() is not None,
        "cartography": get_cartography() is not None,
        "connectivity": get_connectivity() is not None,
        "infra_root": str(get_infrastructure_root()),
    }
