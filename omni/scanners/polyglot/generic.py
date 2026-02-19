"""
Generic Polyglot Project Scanner
================================
Detects projects in languages not covered by specialized scanners.

Supported Ecosystems (via Markers):
- Go (go.mod)
- Java / Kotlin (pom.xml, build.gradle, build.gradle.kts)
- .NET / C# (*.csproj, *.sln)
- Docker (Dockerfile, docker-compose.yml)
- Terraform (*.tf)

This scanner is fully data-driven and can be easily extended.
"""

from pathlib import Path
from typing import Dict, List, Any
from omni.lib.files import walk_project

# Definition of what constitutes a project for various ecosystems
PROJECT_MARKERS = {
    "go": {"go.mod"},
    "java": {"pom.xml", "build.gradle", "build.gradle.kts"},
    "dotnet": {".csproj", ".sln"}, # Extension based
    "docker": {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"},
    "terraform": {".tf"} # Extension based
}

def scan(target: Path) -> Dict[str, Any]:
    """
    Scan for generic projects derived from marker files.
    """
    target_path = Path(target).resolve()
    
    projects = []
    
    # We need to look for specific filenames AND specific extensions
    extensions_to_watch = {".tf", ".csproj", ".sln", ".xml", ".gradle", ".kts", ".mod", ".yaml", ".yml"}
    # Also files without extensions (Dockerfile) need to be checked by name
    
    if target_path.is_file():
        candidates = [target_path]
    else:
        # Use standardized project walker
        # We walk effectively everything that looks like config, but walk_project filters safely
        candidates = walk_project(target_path, extensions=extensions_to_watch | {".*"}) 
    
    for item in candidates:
        ecosystem = _identify_ecosystem(item)
        if ecosystem:
            projects.append({
                "path": str(item.parent),
                "marker": item.name,
                "ecosystem": ecosystem,
                "name": item.parent.name
            })
            
    # Deduplicate: Multiple markers in same folder (e.g. Dockerfile + docker-compose)
    # Group by path
    grouped = {}
    for p in projects:
        path = p["path"]
        if path not in grouped:
            grouped[path] = {
                "path": path,
                "name": p["name"],
                "ecosystems": set(),
                "markers": []
            }
        grouped[path]["ecosystems"].add(p["ecosystem"])
        grouped[path]["markers"].append(p["marker"])
        
    final_items = []
    for path, data in grouped.items():
        final_items.append({
            "path": data["path"],
            "name": data["name"],
            "ecosystems": list(data["ecosystems"]),
            "markers": data["markers"]
        })
        
    return {
        "count": len(final_items),
        "items": final_items,
        "summary": {
            "total_projects": len(final_items),
            "ecosystems_found": list(set(e for item in final_items for e in item["ecosystems"]))
        }
    }

def _identify_ecosystem(path: Path) -> str:
    name = path.name
    suffix = path.suffix
    
    # Exact Name Matching
    for sco, markers in PROJECT_MARKERS.items():
        if name in markers:
            return sco
            
    # Extension Matching
    if suffix == ".csproj" or suffix == ".sln":
        return "dotnet"
    if suffix == ".tf":
        return "terraform"
        
    return None
