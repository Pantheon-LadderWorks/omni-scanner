import os
import re
from pathlib import Path

from omni.core import config
from omni.core.paths import should_skip_path

# --- CONFIGURATION ---
# Load from config or fall back to defaults
conf = config.load_config()
scan_conf = conf.get("scan", {})
GLOBAL_EXCLUDES = {
    "dirs": scan_conf.get("exclude", []),
    "phrases": [
        "site-packages", 
        "superseded",
        "backup", 
        "deprecated",
        "_old",
        "dungeon-map-mlp", 
        "sw.js",
        "governance/registry/surfaces",  # Don't scan previous scan results!
        "omni/artifacts"  # Don't scan Omni's own output
    ]
}

CONTRACT_FAMILIES = {
    "mcp": {
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\mcp\C-MCP-BASE-001.md",
        "status": "partial" 
    },
    "http": {
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\http\C-HTTP-BASE-001.md",
        "status": "partial" 
    },
    "cli": {
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\cli\C-CLI-BASE-001.md",
        "status": "partial"
    },
    "bus_topic": {
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\system\C-SYS-BUS-001_Quadruplet_Crown_Bus.md",
        "status": "partial"
    },
    "db": {
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\db\C-DB-BASE-001.md",
        "status": "partial"
    },
    "doc": { 
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\artifacts\C-ARTIFACT-BASE-001.md",
        "status": "partial"
    },
    "ui_integration": {
        "ref": r"C:\Users\kryst\Infrastructure\governance\contracts\ui\C-UI-BASE-001.md",
        "status": "partial"
    }
}

PATTERNS = {
    "http": [
        r"@app\.(get|post|put|delete|patch)\(",
        r"router\.(get|post|put|delete|patch)\(",
        r"api\.add_resource\(",
        r"class .*\(.*Resource.*\):"
    ],
    "mcp": [
        r"@mcp\.tool",
        r"@mcp\.resource",
        r"class .*Server.*:",
        r"tools\s*=\s*\[",
        r"ListToolsRequest",
        r"CallToolRequest"
    ],
    "cli": [
        r"if __name__ == .__main__.:",
        r"@click\.command",
        r"typer\.Typer\(",
        r"argparse\.ArgumentParser\("
    ],
    "bus_topic": [
        r"publish\(",
        r"subscribe\(",
        r"topic\s*[:=]",
        r"crown://"
    ],
    "db": [
        r"class .*\(.*Model.*\):",
        r"CREATE TABLE"
    ],
    "ui_integration": [
        r"fetch\(",
        r"axios\."
    ]
}

# --- LOGIC ---

def check_project_contracts(project_path_str: str):
    contracts = {"openapi": False, "contracts_dir": False, "system_contract": False}
    
    # SYSTEM CONTRACT CHECK (Hardcoded known system paths map to projects)
    if "orchestration" in project_path_str.lower():
         if os.path.exists(r"C:\Users\kryst\Infrastructure\governance\contracts\system\C-SYS-ORCH-001_UCOE_Core.md"):
             contracts["system_contract"] = True
    
    if os.path.exists(project_path_str):
        for f in os.listdir(project_path_str):
            if f.lower() in ['openapi.yaml', 'openapi.json', 'swagger.yaml', 'swagger.json']:
                contracts["openapi"] = True
            if f.lower() in ['contracts', 'schemas'] and os.path.isdir(os.path.join(project_path_str, f)):
                contracts["contracts_dir"] = True
            if f == "CONTRACT.md":
                contracts["contracts_dir"] = True 
            if f.lower() in ['contracts.py', 'protocols.py']:
                contracts["contracts_dir"] = True
    return contracts

def scan(target: Path) -> dict:
    """
    Recursive scan for Federation Surfaces.
    Returns: { "items": [surfaces], "count": N, "gaps": [gaps] }
    """
    found_surfaces = []
    
    # Resolve target and surface root
    target_path = Path(target).resolve()
    surface_root = target_path if target_path.is_dir() else target_path.parent
    
    # Project Info Inference (Simulated for single project scan)
    project_name = surface_root.name
    project_path_str = str(surface_root.absolute())
    
    # Check Contracts
    contract_meta = check_project_contracts(project_path_str)
    
    # Walk
    for root, dirs, files in os.walk(surface_root):
        root_path = Path(root)
        
        # Skip paths using federation cartography
        if should_skip_path(root_path):
            dirs[:] = []  # Don't descend
            continue
            
        # Excludes
        dirs[:] = [d for d in dirs if d not in GLOBAL_EXCLUDES['dirs'] and not d.startswith('.')]
        
        for file in files:
            if not file.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java')):
                continue
                
            file_path = os.path.join(root, file)
            # Phrase Excludes
            if any(p in file_path.replace("\\", "/") for p in GLOBAL_EXCLUDES["phrases"]):
                continue
                
            # Scan Content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for kind, regexes in PATTERNS.items():
                    for regex in regexes:
                        matches = re.finditer(regex, content)
                        for match in matches:
                            lineno = content[:match.start()].count('\n') + 1
                            
                            # Heuristics & Status (Migrated)
                            contract_status = "missing"
                            
                            if kind == 'http' and contract_meta['openapi']:
                                contract_status = "partial" # Upgrade logic below
                            if kind == 'mcp' and ('inputSchema' in content or 'outputSchema' in content):
                                contract_status = "partial"
                            if kind == 'bus_topic' and 'crown://' in match.group(0):
                                 contract_status = "partial"
                            if "contracts" in file_path or "schema" in file_path:
                                contract_status = "exists"
                                
                            if contract_meta['contracts_dir'] or contract_meta['system_contract']:
                                if contract_status == "missing":
                                    contract_status = "partial"
                            
                            # Family Linking
                            contract_ref = None
                            if kind in CONTRACT_FAMILIES:
                                fam = CONTRACT_FAMILIES[kind]
                                if contract_status == 'missing':
                                    contract_status = fam['status']
                                contract_ref = fam['ref']
                                
                            # Special Upgrade Logic
                            if kind == 'http' and contract_meta['openapi']:
                                contract_status = 'exists'
                            
                            # Scribe Anvil Hack
                            if "scribes-anvil" in project_name.lower() and kind == 'mcp':
                                contract_ref = f"{CONTRACT_FAMILIES['mcp']['ref']} + C-MCP-SCRIBE-001"
                                contract_status = "exists"

                            # Scope
                            scope = "internal"
                            if "external-frameworks" in str(target) or "external" in project_name: # simplified
                                scope = "external_reference"
                            if "Serena" in project_name:
                                scope = "external_reference"

                            found_surfaces.append({
                                "surface_id": f"{project_name}:{file}:{kind}:{lineno}",
                                "kind": kind,
                                "project": project_name,
                                "location": f"{file}:{lineno}",
                                "status": contract_status,
                                "ref": contract_ref,
                                "scope": scope
                            })
                            break # One match per kind per file is enough usually
                            
            except Exception:
                pass

    # Semantic Organization
    organized = _organize_surfaces(found_surfaces)
    
    return {
        "count": len(found_surfaces),
        "items": found_surfaces,
        "organized": organized
    }


def _organize_surfaces(surfaces: list) -> dict:
    """
    Semantically organize surfaces for human comprehension.
    
    Groups by:
    - Kind (MCP, HTTP, CLI, DB, Bus, UI, Doc)
    - Component/Module
    - Status (missing, partial, exists)
    - Contract Family
    """
    by_kind = {}
    by_component = {}
    by_status = {"missing": [], "partial": [], "exists": []}
    by_contract = {}
    
    for surf in surfaces:
        kind = surf["kind"]
        location = surf["location"]
        status = surf["status"]
        contract_ref = surf.get("ref")
        
        # Extract component from location (file:line -> file)
        component = location.split(":")[0].replace(".py", "").replace(".js", "").replace(".ts", "")
        
        # Group by kind
        if kind not in by_kind:
            by_kind[kind] = []
        by_kind[kind].append(surf)
        
        # Group by component
        if component not in by_component:
            by_component[component] = []
        by_component[component].append(surf)
        
        # Group by status
        by_status[status].append(surf)
        
        # Group by contract family
        if contract_ref:
            contract_name = contract_ref.split("\\")[-1].replace(".md", "") if "\\" in contract_ref else "unknown"
            if contract_name not in by_contract:
                by_contract[contract_name] = []
            by_contract[contract_name].append(surf)
    
    # Generate summary statistics
    kind_stats = {k: len(v) for k, v in by_kind.items()}
    component_stats = {k: len(v) for k, v in sorted(by_component.items(), key=lambda x: -len(x[1]))[:20]}  # Top 20 components
    status_stats = {k: len(v) for k, v in by_status.items()}
    contract_stats = {k: len(v) for k, v in by_contract.items()}
    
    return {
        "by_kind": {
            "summary": kind_stats,
            "details": by_kind
        },
        "by_component": {
            "summary": component_stats,
            "details": by_component
        },
        "by_status": {
            "summary": status_stats,
            "details": by_status
        },
        "by_contract": {
            "summary": contract_stats,
            "details": by_contract
        },
        "insights": {
            "total_components": len(by_component),
            "most_surfaced_component": max(by_component.items(), key=lambda x: len(x[1]))[0] if by_component else None,
            "coverage_ratio": round(status_stats["exists"] / (status_stats["exists"] + status_stats["partial"] + status_stats["missing"]) * 100, 1) if surfaces else 0,
            "top_5_components": [k for k, v in sorted(by_component.items(), key=lambda x: -len(x[1]))[:5]]
        }
    }
