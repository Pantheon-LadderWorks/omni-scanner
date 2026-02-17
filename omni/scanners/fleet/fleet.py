"""
Fleet Registry Generator - Omni Scanner
Automatically generates fleet_registry.json files for stations based on their type.

Dynamically loads station-specific configs from fleet_configs/ directory.
Each station can have custom fleet generation logic.

Usage:
    python -m omni.core.scanners.fleet --station=satellite-control --test
    python -m omni.core.scanners.fleet --all
    python -m omni.core.scanners.fleet --station=codecraft
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from omni.core.model import ScanResult
from omni.core import paths
from .fleet_configs import get_fleet_generator, list_available_configs

def generate_nexus_fleet() -> Dict[str, Any]:
    """Generate Nexus fleet from all registered stations."""
    # Nexus orchestrates all stations - use CartographyPillar to read registry
    try:
        from federation_heart.pillars.cartography import CartographyPillar
        cartography = CartographyPillar()
        stations = cartography.get_registry("stations")
    except Exception:
        stations = None
    
    fleet = {
        "station_id": "station-nexus",
        "version": "1.0.0",
        "description": "Seven-Point Star orchestrator - commands all Federation stations",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fleet_type": "stations",
        "servers": []
    }
    
    if stations and "stations" in stations:
        for station in stations["stations"]:
            if station["id"] == "station-nexus":
                continue  # Don't include self
            
            fleet["servers"].append({
                "id": station["id"],
                "name": station["name"],
                "type": station["type"],
                "description": station["description"],
                "status": "registered"
            })
    
    return fleet

def generate_codecraft_fleet() -> Dict[str, Any]:
    """Generate CodeCraft fleet from pip-installed MCP servers."""
    fleet = {
        "station_id": "station-codecraft",
        "version": "1.0.0",
        "description": "CodeCraft Station - 3 MCP servers for ritual pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fleet_type": "mcp_servers",
        "servers": [
            {
                "id": "lexicon",
                "name": "Lexicon MCP Server",
                "role": "analyzer",
                "pillar": "Ethics & Safety (Judge/Scribe)",
                "runtime": "python_mcp",
                "command": "lexicon-mcp",
                "host": "localhost",
                "port": 7001,
                "source": "pip",
                "location": "federation-lexicon-mcp (pip package)",
                "tools": ["validate_codecraft", "canonize_codecraft"],
                "description": "Constitutional validator - Judge mode detects violations, Scribe mode auto-canonizes rituals"
            },
            {
                "id": "codeverter",
                "name": "CodeVerter MCP Server",
                "role": "generator",
                "pillar": "Genesis / Blueprinting (Arcane Weaver)",
                "runtime": "python_mcp",
                "command": "codeverter-mcp",
                "host": "localhost",
                "port": 7002,
                "source": "pip",
                "location": "federation-codeverter-mcp (pip package)",
                "tools": ["convert_code_to_codecraft"],
                "description": "Dual-engine ritual generator - Arcane Weaver (Gemini) + Clockwork Scribe (local transpiler)"
            },
            {
                "id": "native-embassy",
                "name": "CodeCraft Native Embassy",
                "role": "executor",
                "pillar": "Execution / Ghost Fingers (Rust VM)",
                "runtime": "python_mcp",
                "command": "embassy-mcp",
                "host": "localhost",
                "port": 7003,
                "source": "pip",
                "location": "federation-embassy-mcp (pip package)",
                "tools": ["execute_codecraft_ritual"],
                "description": "Constitutional execution gateway - validates and executes .ccraft rituals"
            }
        ]
    }
    
    return fleet

def generate_satellite_control_fleet() -> Dict[str, Any]:
    """Generate Satellite Control fleet from guilds."""
    fleet = {
        "station_id": "station-satellite-control",
        "version": "1.0.0",
        "description": "Satellite Control Station - orchestrates guild satellites",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fleet_type": "guild_satellites",
        "servers": []
    }
    
    # Scan guilds directory for satellites using omni paths
    satellite_station = paths.get_station_path("satellite_control_station")
    if not satellite_station:
        return fleet
    
    guilds_dir = satellite_station / "guilds"
    
    if guilds_dir.exists():
        for guild_dir in guilds_dir.iterdir():
            if not guild_dir.is_dir() or guild_dir.name.startswith('.') or guild_dir.name.startswith('__'):
                continue
            
            # 1. Check for guild leader at root
            guild_leader_file = guild_dir / f"{guild_dir.name}_leader.py"
            if guild_leader_file.exists():
                fleet["servers"].append({
                    "id": f"{guild_dir.name}_leader",
                    "name": f"{guild_dir.name.replace('_', ' ').title()} Leader",
                    "type": "guild_leader",
                    "guild": guild_dir.name,
                    "source": "attach",
                    "location": f"guilds/{guild_dir.name}/{guild_leader_file.name}",
                    "status": "available",
                    "capabilities": ["guild_coordination", "satellite_management"]
                })
            
            # 2. Look for satellite subdirectories in guild
            satellites = list(guild_dir.glob("*_satellite"))
            for satellite_dir in satellites:
                satellite_name = satellite_dir.name.replace("_satellite", "")
                fleet["servers"].append({
                    "id": f"{guild_dir.name}.{satellite_name}",
                    "name": f"{satellite_name.title()} Satellite",
                    "type": "guild_satellite",
                    "guild": guild_dir.name,
                    "source": "attach",
                    "location": f"guilds/{guild_dir.name}/{satellite_dir.name}",
                    "status": "registered",
                    "capabilities": []
                })
    
    return fleet

FLEET_GENERATORS = {
    "station-nexus": generate_nexus_fleet,
    "station-codecraft": generate_codecraft_fleet,
    "station-satellite-control": generate_satellite_control_fleet,
}


def scan(target_path: Path) -> ScanResult:
    """
    Generate fleet registries for stations using dynamic config modules.
    
    Usage:
        omni scan fleet --all                    # Generate all supported fleet registries
        omni scan fleet --station=nexus          # Generate specific station
        omni scan fleet --station=codecraft
        omni scan fleet --station=satellite_control --test   # Test mode (outputs to .test.json)
    """
    import sys
    
    # Parse command-line args (sys.argv since omni CLI doesn't forward custom args)
    test_mode = "--test" in sys.argv
    generate_all = "--all" in sys.argv
    station_arg = None
    
    for arg in sys.argv:
        if arg.startswith("--station="):
            station_arg = arg.split("=")[1]
    
    # Determine which stations to generate
    stations_to_generate = []
    
    if generate_all:
        # Get all available configs
        stations_to_generate = list(list_available_configs().keys())
    elif station_arg:
        # Normalize station ID format
        if not station_arg.startswith("station-"):
            station_arg = f"station-{station_arg}"
        stations_to_generate = [station_arg]
    else:
        return ScanResult(
            target=str(target_path),
            version="0.1",
            timestamp=datetime.now().isoformat(),
            findings={"generated": [], "errors": ["No station specified. Use --all or --station=<name>"]},
            summary={"count": 0, "test_mode": test_mode, "status": "error"}
        )
    
    # Get CartographyPillar for stations that need it
    try:
        from federation_heart.pillars.cartography import CartographyPillar
        cartography = CartographyPillar()
    except ImportError:
        cartography = None
    
    # Registry root for writing fleet files
    registry_root = paths.get_governance_path("registry/stations")
    if not registry_root:
        return ScanResult(
            target=str(target_path),
            version="0.1",
            timestamp=datetime.now().isoformat(),
            findings={"generated": [], "errors": ["Cannot resolve governance/registry/stations path"]},
            summary={"count": 0, "test_mode": test_mode, "status": "error"}
        )
    
    generated = []
    errors = []
    
    for station_id in stations_to_generate:
        try:
            # Get the fleet generator for this station
            generator = get_fleet_generator(station_id)
            if not generator:
                errors.append(f"No fleet config found for {station_id}")
                continue
            
            # Get station path (some configs need it)
            station_folder = station_id.replace("station-", "").replace("-", "_")
            station_path = paths.get_station_path(f"{station_folder}_station")
            
            # Generate fleet data using the config's generator
            fleet_data = generator(station_path=station_path, cartography_pillar=cartography)
            
            # Determine output path
            output_filename = "fleet_registry.test.json" if test_mode else "fleet_registry.json"
            output_path = registry_root / station_folder / output_filename
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write fleet registry
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(fleet_data, f, indent=2, ensure_ascii=False)
            
            generated.append({
                "station": station_id,
                "path": str(output_path),
                "fleet_type": fleet_data.get("fleet_type"),
                "server_count": len(fleet_data.get("servers", []))
            })
            
        except Exception as e:
            errors.append(f"{station_id}: {str(e)}")
    
    return ScanResult(
        target=str(target_path),
        version="0.1",
        timestamp=datetime.now().isoformat(),
        findings={"generated": generated, "errors": errors},
        summary={
            "count": len(generated),
            "test_mode": test_mode,
            "status": "success" if generated and not errors else "error"
        }
    )
    result = ScanResult(target=str(target_path))
    errors = []
    findings = []
    
    # Determine which stations to generate
    import sys
    generate_all = "--all" in sys.argv
    test_mode = "--test" in sys.argv
    station_arg = next((arg for arg in sys.argv if arg.startswith("--station=")), None)
    
    stations_to_generate = []
    if generate_all:
        stations_to_generate = list(FLEET_GENERATORS.keys())
    elif station_arg:
        station_id = f"station-{station_arg.split('=')[1]}"
        if station_id in FLEET_GENERATORS:
            stations_to_generate = [station_id]
        else:
            errors.append(f"No fleet generator for {station_id}")
            result.findings = {"errors": errors}
            result.summary = {"status": "error"}
            return result
    else:
        errors.append("Specify --all or --station=<name>")
        result.findings = {"errors": errors}
        result.summary = {"status": "error"}
        return result
    
    # Generate registries
    registry_root = paths.get_governance_path("registry/stations")
    if not registry_root:
        errors.append("Cannot resolve governance/registry/stations path")
        result.findings = {"errors": errors}
        result.summary = {"status": "error"}
        return result
    
    for station_id in stations_to_generate:
        try:
            fleet_data = FLEET_GENERATORS[station_id]()
            # Station folders use underscores, station IDs use hyphens
            station_folder = station_id.replace("station-", "").replace("-", "_")
            
            # Test mode outputs to .test.json file
            if test_mode:
                output_path = registry_root / station_folder / "fleet_registry.test.json"
            else:
                output_path = registry_root / station_folder / "fleet_registry.json"
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(fleet_data, f, indent=2, ensure_ascii=False)
            
            findings.append({
                "station": station_id,
                "path": str(output_path),
                "fleet_type": fleet_data.get("fleet_type"),
                "server_count": len(fleet_data.get("servers", []))
            })
        except Exception as e:
            errors.append(f"{station_id}: {e}")
    
    result.findings = {"generated": findings, "errors": errors}
    result.summary = {
        "count": len(findings),
        "test_mode": test_mode,
        "status": "success" if not errors else "partial"
    }
    return result
