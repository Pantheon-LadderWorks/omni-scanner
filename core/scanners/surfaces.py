import os
import re
from pathlib import Path

# --- CONFIGURATION (Ported from surface_scanner.py) ---

GLOBAL_EXCLUDES = {
    "dirs": [
        "node_modules", ".git", ".venv", "venv", "env", "site-packages", 
        "dist", "build", "__pycache__", ".pytest_cache", ".mypy_cache", 
        ".next", ".swc", "out", "android", "ios", ".firebase", ".expo", 
        ".idea", ".vscode", "coverage"
    ],
    "phrases": [
        "site-packages", 
        "superseded",
        "backup",
        "deprecated",
        "_old",
        "dungeon-map-mlp", 
        "sw.js" 
    ]
}

CONTRACT_FAMILIES = {
    "mcp": {
        "ref": r"C:\Users\kryst\Infrastructure\contracts\mcp\C-MCP-BASE-001.md",
        "status": "partial" 
    },
    "http": {
        "ref": r"C:\Users\kryst\Infrastructure\contracts\http\C-HTTP-BASE-001.md",
        "status": "partial" 
    },
    "cli": {
        "ref": r"C:\Users\kryst\Infrastructure\contracts\cli\C-CLI-BASE-001.md",
        "status": "partial"
    },
    "bus_topic": {
        "ref": r"C:\Users\kryst\Infrastructure\contracts\system\C-SYS-BUS-001_Quadruplet_Crown_Bus.md",
        "status": "partial"
    },
    "db": {
        "ref": r"C:\Users\kryst\Infrastructure\contracts\db\C-DB-BASE-001.md",
        "status": "partial"
    },
    "doc": { 
        "ref": r"C:\Users\kryst\Infrastructure\contracts\artifacts\C-ARTIFACT-BASE-001.md",
        "status": "partial"
    },
    "ui_integration": {
        "ref": r"C:\Users\kryst\Infrastructure\contracts\ui\C-UI-BASE-001.md",
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
         if os.path.exists(r"C:\Users\kryst\Infrastructure\contracts\system\C-SYS-ORCH-001_UCOE_Core.md"):
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
    
    # Project Info Inference (Simulated for single project scan)
    project_name = target.name
    project_path_str = str(target.absolute())
    
    # Check Contracts
    contract_meta = check_project_contracts(project_path_str)
    
    # Walk
    for root, dirs, files in os.walk(target):
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

    return {
        "count": len(found_surfaces),
        "items": found_surfaces
    }
