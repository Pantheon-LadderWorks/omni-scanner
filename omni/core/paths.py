"""
🗺️ Federation Paths - Canonical Path Resolution

Central integration point using federation_heart's CartographyPillar.
All scanners should use this module to get canonical Federation paths.

Usage:
    from omni.core.paths import get_governance_path, get_infrastructure_root

Author: Oracle + Federation Heart Integration
Version: 1.1.0 - Uses CartographyPillar for proper client routing
"""

from pathlib import Path
from typing import Optional

# Federation Heart Integration via CartographyPillar
_cartography = None
_federation_available = False

try:
    from federation_heart.pillars.cartography import CartographyPillar
    _cartography = CartographyPillar()
    _federation_available = True
except ImportError:
    _federation_available = False


def is_federation_available() -> bool:
    """Check if federation_heart is available."""
    return _federation_available


def get_infrastructure_root() -> Optional[Path]:
    """Get Infrastructure root path from CartographyPillar."""
    if not _federation_available or not _cartography:
        return None
    return _cartography.get_infrastructure_root()


def get_governance_path(subpath: str = "") -> Optional[Path]:
    """
    Get governance/ path from CartographyPillar.
    
    Args:
        subpath: Optional subpath within governance/ (e.g., "registry/surfaces")
    
    Returns:
        Path to governance/ or governance/subpath, or None if unavailable
    """
    if not _federation_available or not _cartography:
        return None
    
    gov_path = _cartography.resolve_path("governance")
    if not gov_path:
        return None
    
    if subpath:
        return gov_path / subpath
    return gov_path


def get_station_path(station_name: str = "") -> Optional[Path]:
    """
    Get stations/ path from CartographyPillar.
    
    Args:
        station_name: Optional station name (e.g., "satellite_control_station")
    
    Returns:
        Path to stations/ or stations/{station_name}, or None if unavailable
    """
    if not _federation_available or not _cartography:
        return None
    
    stations_path = _cartography.resolve_path("stations")
    if not stations_path:
        return None
    
    if station_name:
        return stations_path / station_name
    return stations_path


def get_agent_path(agent_name: str = "") -> Optional[Path]:
    """
    Get agents/ path from federation_heart.
    
    Args:
        agent_name: Optional agent name (e.g., "oracle-agent")
    
    Returns:
        Path to agents/ or agents/{agent_name}, or None if unavailable
    """
    if not _federation_available or not _registry_client:
        return None
    try:
        agents_path = _registry_client.resolve_path("infrastructure") / "agents"
        if agent_name:
            return agents_path / agent_name
        return agents_path
    except Exception:
        return None


def get_memory_path(subpath: str = "") -> Optional[Path]:
    """
    Get memory-substrate/ path from federation_heart.
    
    Args:
        subpath: Optional subpath within memory-substrate/
    
    Returns:
        Path to memory-substrate/ or memory-substrate/subpath, or None if unavailable
    """
    if not _federation_available or not _registry_client:
        return None
    try:
        memory_path = _registry_client.resolve_path("infrastructure") / "memory-substrate"
        if subpath:
            return memory_path / subpath
        return memory_path
    except Exception:
        return None


def get_orchestration_path(subpath: str = "") -> Optional[Path]:
    """
    Get orchestration/ path from federation_heart.
    
    Args:
        subpath: Optional subpath within orchestration/
    
    Returns:
        Path to orchestration/ or orchestration/subpath, or None if unavailable
    """
    if not _federation_available or not _registry_client:
        return None
    try:
        orch_path = _registry_client.resolve_path("infrastructure") / "orchestration"
        if subpath:
            return orch_path / subpath
        return orch_path
    except Exception:
        return None


# Convenience function for scanners to check if they should skip a path
def should_skip_path(path: Path) -> bool:
    """
    Check if a path should be skipped during scans.
    
    Automatically excludes:
    - governance/registry/surfaces/ (previous scan results)
    - omni/artifacts/ (Omni's own output)
    
    Args:
        path: Path to check
    
    Returns:
        True if path should be skipped
    """
    if not isinstance(path, Path):
        path = Path(path)
    
    # Check governance surfaces registry
    surfaces_path = get_governance_path("registry/surfaces")
    if surfaces_path and (path == surfaces_path or surfaces_path in path.parents):
        return True
    
    # Check omni artifacts
    if "omni" in path.parts and "artifacts" in path.parts:
        return True
    
    return False
