"""
Core Scanner
Discovers all *_core.py files across Infrastructure and validates against registry.
Uses omni.core.paths for canonical path resolution.
"""
from pathlib import Path
from typing import Dict, Any, List
import re

# Use omni's canonical path resolution
from omni.core.paths import get_infrastructure_root, is_federation_available


def scan(target: Path) -> dict:
    """
    Scan for *_core.py files across Infrastructure.
    
    Args:
        target: Path to scan (typically Infrastructure root)
        
    Returns:
        dict with discovered cores, categorized by tier
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "cores",
            "version": "1.0.0",
            "description": "Federation Core discovery scanner"
        },
        "summary": {
            "total_cores": 0,
            "federation_cores": 0,
            "station_cores": 0,
            "agent_cores": 0,
            "mcp_cores": 0,
            "other_cores": 0
        }
    }
    
    try:
        # Use omni's canonical path resolution (routes through CartographyPillar)
        infra_root = get_infrastructure_root()
        if not infra_root:
            # Fallback if federation_heart not available
            infra_root = find_infrastructure_root(target)
        
        if not infra_root:
            results["metadata"]["error"] = "Infrastructure root not found"
            results["metadata"]["federation_available"] = is_federation_available()
            return results
        

        # Scan for *_core.py files using shared utility
        from omni.lib.files import walk_project
        
        core_files = []
        # extensions=None because we want specific pattern matching, not just extension
        for file_path in walk_project(infra_root, extensions=['.py']):
            if file_path.name.endswith("_core.py"):
                # Check exclusion patterns manually since walk_project handles dirs but not file patterns
                # Actually walk_project handles standard dir excludes. 
                # We just need to check the file name pattern.
                if "test_" in file_path.name:
                    continue
                    
                core_files.append(file_path)
        
        # Categorize cores
        for core_file in core_files:
            rel_path = str(core_file.relative_to(infra_root)).replace("\\", "/")
            
            # Determine tier
            tier = categorize_core(rel_path)
            
            # Extract core name from filename
            core_name = core_file.stem  # e.g., "federation_core"
            
            # Try to extract class name
            class_name = extract_core_class(core_file)
            
            core_info = {
                "path": rel_path,
                "name": core_name,
                "class_name": class_name,
                "tier": tier,
                "exists": True,
                "size_bytes": core_file.stat().st_size
            }
            
            results["items"].append(core_info)
            
            # Update summary counts
            results["summary"]["total_cores"] += 1
            if tier == "T0-Federation":
                results["summary"]["federation_cores"] += 1
            elif tier == "T1-Station":
                results["summary"]["station_cores"] += 1
            elif tier in ["T3-Agent", "T4-Crown"]:
                results["summary"]["agent_cores"] += 1
            elif tier == "T2-MCP":
                results["summary"]["mcp_cores"] += 1
            else:
                results["summary"]["other_cores"] += 1
        
        results["count"] = len(results["items"])
        
    except Exception as e:
        results["metadata"]["error"] = f"Core scan failed: {str(e)}"
    
    return results


def categorize_core(rel_path: str) -> str:
    """Categorize a core file by its path."""
    
    # Federation Infrastructure Cores
    if "federation_heart/core" in rel_path or "federation_core" in rel_path:
        return "T0-Federation"
    if "orchestration/" in rel_path:
        return "T0-Federation"
    
    # Station Cores
    if "stations/" in rel_path:
        return "T1-Station"
    
    # MCP/Tool Cores
    if "mcp-servers/" in rel_path:
        return "T2-MCP"
    if "conversation-memory-project/" in rel_path:
        return "T2-MCP"
    
    # Agent Cores
    if "crown-agents/" in rel_path:
        return "T4-Crown"
    if "agents/" in rel_path:
        return "T3-Agent"
    
    return "Other"


def extract_core_class(core_file: Path) -> str:
    """Try to extract the main class name from a core file."""
    try:
        content = core_file.read_text(encoding="utf-8", errors="ignore")
        
        # Look for class definitions
        class_pattern = r"class\s+(\w+Core)\s*[:\(]"
        matches = re.findall(class_pattern, content)
        
        if matches:
            return matches[0]  # Return first *Core class
        
        # Fallback: any class definition
        any_class_pattern = r"class\s+(\w+)\s*[:\(]"
        matches = re.findall(any_class_pattern, content)
        if matches:
            return matches[0]
            
    except Exception:
        pass
    
    return "Unknown"


def find_infrastructure_root(start_path: Path) -> Path:
    """Find Infrastructure root by looking for federation_heart/."""
    current = start_path if start_path.is_dir() else start_path.parent
    
    # Walk up until we find federation_heart or hit root
    for _ in range(10):  # Safety limit
        if (current / "federation_heart").exists():
            return current
        if (current / "INFRASTRUCTURE_MANIFEST_V1.yaml").exists():
            return current
        
        parent = current.parent
        if parent == current:  # Hit filesystem root
            break
        current = parent
    
    return None


def get_cores_by_tier(target: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get cores organized by tier for easy consumption.
    
    Returns:
        dict mapping tier -> list of core info dicts
    """
    scan_results = scan(target)
    
    by_tier = {
        "T0-Federation": [],
        "T1-Station": [],
        "T2-MCP": [],
        "T3-Agent": [],
        "T4-Crown": [],
        "Other": []
    }
    
    for item in scan_results.get("items", []):
        tier = item.get("tier", "Other")
        if tier in by_tier:
            by_tier[tier].append(item)
        else:
            by_tier["Other"].append(item)
    
    return by_tier


# CLI entry point for testing
if __name__ == "__main__":
    import json
    from pathlib import Path
    
    # Scan from current directory
    target = Path.cwd()
    results = scan(target)
    
    print(f"🔍 Core Scanner Results")
    print(f"=" * 50)
    print(f"Total cores found: {results['count']}")
    print(f"Summary: {json.dumps(results['summary'], indent=2)}")
    print()
    
    # Print by tier
    by_tier = get_cores_by_tier(target)
    for tier, cores in by_tier.items():
        if cores:
            print(f"\n{tier}: ({len(cores)} cores)")
            for core in cores:
                print(f"  - {core['name']}: {core['path']}")
