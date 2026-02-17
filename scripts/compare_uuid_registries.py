"""
Compare PROJECT_REGISTRY_V1.yaml UUIDs with canonical_uuids.json
Find missing projects and show what needs to be added to canonical.
"""
import json
import yaml
from pathlib import Path
from collections import defaultdict

# Paths
INFRA = Path(r"C:\Users\kryst\Infrastructure")
REGISTRY_PATH = INFRA / "governance/registry/projects/PROJECT_REGISTRY_V1.yaml"
CANONICAL_PATH = INFRA / "governance/registry/uuid/canonical_uuids.json"

def load_data():
    """Load both registries."""
    with open(REGISTRY_PATH, encoding='utf-8') as f:
        registry = yaml.safe_load(f)
    
    with open(CANONICAL_PATH, encoding='utf-8') as f:
        canonical = json.load(f)
    
    return registry, canonical

def analyze():
    """Find UUID gaps."""
    registry, canonical = load_data()
    
    # Get all project UUIDs from each source
    reg_projects = {p['uuid']: p for p in registry['projects']}
    canon_projects = {uuid: data for uuid, data in canonical.items() 
                      if data.get('type') in ['PROJECT', 'REPO']}
    
    # Find overlaps and gaps
    reg_uuids = set(reg_projects.keys())
    canon_uuids = set(canon_projects.keys())
    
    overlap = reg_uuids & canon_uuids
    in_reg_only = reg_uuids - canon_uuids
    in_canon_only = canon_uuids - reg_uuids
    
    print("=" * 80)
    print("📊 UUID REGISTRY COMPARISON")
    print("=" * 80)
    print(f"  Registry (PROJECT_REGISTRY_V1.yaml): {len(reg_uuids)} projects")
    print(f"  Canonical (canonical_uuids.json):    {len(canon_uuids)} projects")
    print(f"  Overlap:                              {len(overlap)} projects")
    print(f"  In registry but NOT canonical:        {len(in_reg_only)} projects")
    print(f"  In canonical but NOT registry:        {len(in_canon_only)} projects")
    print()
    
    if overlap > 0:
        print(f"✅ {len(overlap)} projects found in BOTH registries")
    else:
        print(f"🚨 ZERO OVERLAP - Different UUID namespaces detected!")
    print()
    
    # Show sample missing projects (in registry but not canonical)
    if in_reg_only:
        print(f"🔥 Sample projects IN REGISTRY but MISSING from canonical_uuids.json:")
        print()
        for uuid in sorted(in_reg_only)[:10]:
            proj = reg_projects[uuid]
            print(f"  UUID: {uuid}")
            print(f"    Name: {proj['name']}")
            print(f"    Display: {proj['display_name']}")
            print(f"    GitHub: {proj.get('github_url', 'N/A')}")
            print(f"    Local: {len(proj.get('local_paths', []))} path(s)")
            print()
        
        if len(in_reg_only) > 10:
            print(f"  ... and {len(in_reg_only) - 10} more")
    
    # Show projects in canonical but not registry (orphaned?)
    if in_canon_only:
        print()
        print(f"⚠️ Projects IN CANONICAL but NOT in registry (orphaned?):")
        print()
        for uuid in sorted(in_canon_only)[:5]:
            data = canon_projects[uuid]
            print(f"  UUID: {uuid}")
            print(f"    Name: {data.get('name', 'UNKNOWN')}")
            print(f"    Type: {data.get('type')}")
            print()

if __name__ == "__main__":
    analyze()
