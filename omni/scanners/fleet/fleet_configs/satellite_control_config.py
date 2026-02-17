"""
Fleet generation config for Satellite Control Station.

This config defines how to scan and generate the fleet registry for guild-based stations.
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone


def scan_guild_satellites(station_path: Path) -> List[Dict[str, Any]]:
    """
    Scan guilds directory for guild leaders and satellites.
    
    Structure expected:
    guilds/
      {guild_name}/
        {guild_name}_leader.py    # Guild leader
        {satellite_name}_satellite/   # Satellite directories
    """
    servers = []
    guilds_dir = station_path / "guilds"
    
    if not guilds_dir.exists():
        return servers
    
    for guild_dir in guilds_dir.iterdir():
        if not guild_dir.is_dir() or guild_dir.name.startswith('.') or guild_dir.name.startswith('__'):
            continue
        
        # 1. Check for guild leader at root
        guild_leader_file = guild_dir / f"{guild_dir.name}_leader.py"
        if guild_leader_file.exists():
            servers.append({
                "id": f"{guild_dir.name}_leader",
                "name": f"{guild_dir.name.replace('_', ' ').title()} Leader",
                "type": "guild_leader",
                "guild": guild_dir.name,
                "source": "attach",
                "location": f"guilds/{guild_dir.name}/{guild_leader_file.name}",
                "status": "available",
                "capabilities": ["guild_coordination", "satellite_management"]
            })
        
        # 2. Scan for satellite subdirectories
        satellites = list(guild_dir.glob("*_satellite"))
        for satellite_dir in satellites:
            satellite_name = satellite_dir.name.replace("_satellite", "")
            servers.append({
                "id": f"{guild_dir.name}.{satellite_name}",
                "name": f"{satellite_name.title()} Satellite",
                "type": "guild_satellite",
                "guild": guild_dir.name,
                "source": "attach",
                "location": f"guilds/{guild_dir.name}/{satellite_dir.name}",
                "status": "registered",
                "capabilities": []
            })
    
    return servers


# Fleet generation function for this station
def generate_fleet(station_path: Path = None, cartography_pillar=None) -> Dict[str, Any]:
    """Generate fleet registry for Satellite Control Station."""
    if not station_path:
        return {
            "station_id": "station-satellite-control",
            "version": "1.0.0",
            "description": "Satellite Control Station - orchestrates guild satellites",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "fleet_type": "guild_satellites",
            "servers": []
        }
    
    servers = scan_guild_satellites(station_path)
    
    return {
        "station_id": "station-satellite-control",
        "version": "1.0.0",
        "description": "Satellite Control Station - orchestrates guild satellites",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fleet_type": "guild_satellites",
        "servers": servers
    }


# Export metadata about this config
CONFIG_META = {
    "station_id": "station-satellite-control",
    "fleet_type": "guild_satellites",
    "description": "Scans guilds directory for guild leaders and satellite subdirectories"
}
