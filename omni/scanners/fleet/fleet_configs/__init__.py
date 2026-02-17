"""
Fleet configuration modules for different station types.

Each config module exports:
- generate_fleet(station_path, cartography_pillar): Main generation function
- CONFIG_META: Metadata about the config (station_id, fleet_type, description)

To add a new station fleet config:
1. Create {station_name}_config.py in this directory
2. Implement generate_fleet() function
3. Export CONFIG_META dict
4. Import and register in __init__.py
"""
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import importlib

# Station ID → config module name mapping
STATION_CONFIGS = {
    "station-nexus": "nexus_config",
    "station-codecraft": "codecraft_config",
    "station-satellite-control": "satellite_control_config",
}


def get_fleet_generator(station_id: str) -> Optional[Callable]:
    """
    Dynamically load fleet generator for a station.
    
    Args:
        station_id: Station ID (e.g., "station-nexus")
    
    Returns:
        generate_fleet function from the config module, or None if not found
    """
    config_module_name = STATION_CONFIGS.get(station_id)
    if not config_module_name:
        return None
    
    try:
        # Dynamically import the config module
        module = importlib.import_module(f"omni.core.scanners.fleet_configs.{config_module_name}")
        return getattr(module, "generate_fleet", None)
    except (ImportError, AttributeError):
        return None


def get_config_meta(station_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata about a station's fleet config.
    
    Args:
        station_id: Station ID (e.g., "station-nexus")
    
    Returns:
        CONFIG_META dict from the config module, or None if not found
    """
    config_module_name = STATION_CONFIGS.get(station_id)
    if not config_module_name:
        return None
    
    try:
        module = importlib.import_module(f"omni.core.scanners.fleet_configs.{config_module_name}")
        return getattr(module, "CONFIG_META", None)
    except (ImportError, AttributeError):
        return None


def list_available_configs() -> Dict[str, Dict[str, Any]]:
    """
    List all available fleet configs with their metadata.
    
    Returns:
        Dict mapping station_id → CONFIG_META
    """
    configs = {}
    for station_id in STATION_CONFIGS:
        meta = get_config_meta(station_id)
        if meta:
            configs[station_id] = meta
    return configs
