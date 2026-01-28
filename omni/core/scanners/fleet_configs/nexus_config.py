"""
Fleet generation config for Station Nexus.

Generates fleet from the station registry - all registered stations become fleet members.
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone


def scan_registered_stations(cartography_pillar) -> List[Dict[str, Any]]:
    """Load all registered stations from the station registry."""
    servers = []
    
    stations_reg = cartography_pillar.get_registry("stations")
    if not stations_reg:
        return servers
    
    for station in stations_reg.get("stations", []):
        servers.append({
            "id": station.get("id"),
            "name": station.get("name"),
            "type": "station",
            "phase": station.get("phase"),
            "description": station.get("description", ""),
            "status": "registered"
        })
    
    return servers


# Fleet generation function for this station
def generate_fleet(station_path: Path = None, cartography_pillar=None) -> Dict[str, Any]:
    """Generate fleet registry for Station Nexus."""
    if not cartography_pillar:
        try:
            from federation_heart.pillars.cartography import CartographyPillar
            cartography_pillar = CartographyPillar()
        except ImportError:
            return {
                "station_id": "station-nexus",
                "version": "1.0.0",
                "description": "Station Nexus - Federation brain stem",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "fleet_type": "stations",
                "servers": []
            }
    
    servers = scan_registered_stations(cartography_pillar)
    
    return {
        "station_id": "station-nexus",
        "version": "1.0.0",
        "description": "Station Nexus - Federation brain stem",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fleet_type": "stations",
        "servers": servers
    }


# Export metadata about this config
CONFIG_META = {
    "station_id": "station-nexus",
    "fleet_type": "stations",
    "description": "Loads all registered stations from STATION_REGISTRY_MANIFEST_V1.yaml"
}
