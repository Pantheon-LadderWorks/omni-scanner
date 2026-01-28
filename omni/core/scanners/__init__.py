from . import (
    surfaces, docs, deps, contracts, tools, uuids, events, hooks,
    node_scanner, rust_scanner, package_scanner,
    federation_health, station_health, cmp_health, pillar_health, tunnel_status,
    library, fleet, canon, cores,
    cli,  # CLI Command Scanner
    git   # Git Status Scanner
)

# The Plugin Registry
# Add new scanners here to automatically expose them to the CLI
SCANNERS = {
    # Static Scanners (Filesystem)
    "surfaces": surfaces.scan,
    "events": events.scan,
    "docs": docs.scan,
    "deps": deps.scan,
    "contracts": contracts.scan,
    "tools": tools.scan,
    "uuids": uuids.scan,
    "hooks": hooks.scan,
    
    # Polyglot Scanners
    "node": node_scanner.scan,
    "rust": rust_scanner.scan,
    "packages": package_scanner.scan,
    
    # Runtime Health Scanners
    "federation_health": federation_health.scan,
    "station_health": station_health.scan,
    "cmp_health": cmp_health.scan,
    "pillar_health": pillar_health.scan,
    "tunnel_status": tunnel_status.scan,
    
    # Discovery Scanners
    "cores": cores.scan,
    "cli": cli.scan,  # NEW: @command decorator scanner
    
    # Intelligence Scanners (The Grand Librarian)
    "library": library.scan,
    
    # CodeCraft Canon Scanner
    "canon": canon.scan,
    
    # Fleet Registry Generators
    "fleet": fleet.scan,
    
    # Git Status Scanner (Repo Health)
    "git": git.scan,
}

