"""
remediate_registry_identity.py
Description: Fixes the 3 remaining Divergences in Registry (Atlas Forge, Quantum, Scribes Anvil).
             Implements the "Clean Fixes" authorized by Kryssie/Mega.
             - Splits Atlas Forge (Tool vs Project)
             - Assigns correct DB UUID to Quantum
             - Deep Merges Scribes Anvil duplicates
             - Writes to .remediated.md
"""

import yaml
import re
from pathlib import Path

INPUT_PATH  = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.md")
OUTPUT_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.remediated.md")

# DB UUIDs
UUID_ATLAS_FORGE = "f64413b9-1757-4726-8ba9-a061614f1caf"
UUID_QUANTUM     = "37e7248a-5e09-46d5-bb67-2430c3ec720c" 
UUID_SCRIBES     = "babb8667-d9c9-46fb-9215-b7b0a0f24eac"

def assert_uuid_unused(entities, uuid, expected_cid):
    normalized_uuid = uuid.strip().lower()
    for e in entities:
        curr = str(e.get("facets", {}).get("core", {}).get("id", "")).strip().lower()
        if curr == normalized_uuid:
            # If expected_cid is provided, allow it if it matches
            if expected_cid and e.get("canonical_id") == expected_cid:
                continue
            raise SystemExit(f"❌ ABORT: UUID {uuid} already used by {e.get('canonical_id')}")

def deep_merge(target, source):
    for key, val in source.items():
        if key in target:
            if isinstance(target[key], dict) and isinstance(val, dict):
                deep_merge(target[key], val)
            elif isinstance(target[key], list) and isinstance(val, list):
                combined = target[key] + [x for x in val if x not in target[key]]
                target[key] = sorted(list(set(combined))) if all(isinstance(i, str) for i in combined) else combined
            else:
                if not target[key] and val:
                    target[key] = val
        else:
            target[key] = val
    return target

def remediate():
    content = INPUT_PATH.read_text(encoding="utf-8")
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, flags=re.S)
    if not match: 
        print("❌ Frontmatter not found.")
        return
    
    frontmatter_raw = match.group(1)
    md_body = content[match.end():]
    data = yaml.safe_load(frontmatter_raw)
    entities = data.get("entities", [])
    
    print(f"Loaded {len(entities)} entities.")

    # 1. UUID Safety Checks
    print("Checking UUID collisions...")
    assert_uuid_unused(entities, UUID_ATLAS_FORGE, "atlas-forge")
    assert_uuid_unused(entities, UUID_QUANTUM, "quantum-nonary")
    assert_uuid_unused(entities, UUID_SCRIBES, "scribes-anvil")
    print("✅ UUIDs safe to assign.")

    # 2. Apply Fixes
    new_entities = []
    scribes_found = []
    atlas_forge_project_created = False
    
    for e in entities:
        cid = e.get("canonical_id")
        
        # FIX 1: Atlas Forge Split
        if cid == "atlas-forge":
            if e.get("kind") == "tool":
                e["canonical_id"] = "atlas-forge-tool"
                print("✅ Renamed 'atlas-forge' (Tool) -> 'atlas-forge-tool'")
                new_entities.append(e)
                continue
            # If it's already a project (unlikely based on report), allow it to be patched
            elif e.get("kind") == "project":
                # Will patch UUID below if we don't create new one
                pass

        # FIX 2: Quantum Nonary
        if cid == "quantum-nonary":
            if "facets" not in e: e["facets"] = {}
            if "core" not in e["facets"]: e["facets"]["core"] = {}
            e["facets"]["core"]["id"] = UUID_QUANTUM
            print(f"✅ Fixed Quantum Nonary UUID -> {UUID_QUANTUM}")

        # FIX 3: Scribes Anvil Collection
        if cid == "scribes-anvil":
            scribes_found.append(e)
            continue # Don't add to new_list yet
            
        new_entities.append(e)

    # 3. Create/Patch Atlas Forge Project
    # Check if a project 'atlas-forge' exists in new list (it shouldn't if we renamed the tool)
    existing_atlas_proj = next((x for x in new_entities if x["canonical_id"] == "atlas-forge"), None)
    
    if not existing_atlas_proj:
        new_proj = {
            "canonical_id": "atlas-forge",
            "display_name": "Atlas Forge",
            "kind": "project",
            "status": "active",
            "tags": ["Workspace"],
            "facets": {
                "core": {"id": UUID_ATLAS_FORGE},
                "repo": {
                    "primary_repo": "https://github.com/Kryssie6985/atlas-forge",
                    "local_paths": ["game-development/atlas-forge"]
                }
            }
        }
        new_entities.append(new_proj)
        print(f"✅ Created NEW Project Entity: atlas-forge ({UUID_ATLAS_FORGE})")
    else:
        # Patch existing if it was somehow a project
        if "facets" not in existing_atlas_proj: existing_atlas_proj["facets"] = {}
        if "core" not in existing_atlas_proj["facets"]: existing_atlas_proj["facets"]["core"] = {}
        existing_atlas_proj["facets"]["core"]["id"] = UUID_ATLAS_FORGE
        print(f"✅ Patched existing Atlas Forge Project UUID")

    # 4. Process Scribes Anvil Merge
    if scribes_found:
        print(f"Merging {len(scribes_found)} Scribes Anvil duplicates...")
        # Master candidate selection
        master = None
        for s in scribes_found:
            repo = s.get("facets", {}).get("repo", {}).get("primary_repo", "")
            if "github.com" in repo:
                master = s
                break
        
        if not master: master = scribes_found[0]
        
        # Deep Merge
        for s in scribes_found:
            if s is master: continue
            deep_merge(master, s)
            
        # Set UUID
        if "facets" not in master: master["facets"] = {}
        if "core" not in master["facets"]: master["facets"]["core"] = {}
        master["facets"]["core"]["id"] = UUID_SCRIBES
        
        new_entities.append(master)
        print(f"✅ Merged Scribes Anvil -> UUID {UUID_SCRIBES}")
        
    # Sort
    new_entities.sort(key=lambda x: x["canonical_id"])
    data["entities"] = new_entities
    
    # Write Back
    new_yaml = yaml.dump(data, sort_keys=False, width=1000)
    output = "---\n" + new_yaml + "---\n" + md_body
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"✅ Remediation Complete. Written to: {OUTPUT_PATH}")

if __name__ == "__main__":
    remediate()
