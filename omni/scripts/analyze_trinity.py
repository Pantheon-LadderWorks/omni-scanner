import json
import yaml
import re
from pathlib import Path

# --- CONFIGURATION ---
REGISTRY_PATH = Path("../PROJECT_REGISTRY_MASTER.remediated.md")
# Fallback for running from non-root
if not REGISTRY_PATH.exists():
    REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.remediated.md")

DB_DUMP_PATH = Path("artifacts/omni/canonical_uuids.json")
if not DB_DUMP_PATH.exists():
    DB_DUMP_PATH = Path(r"C:\Users\kryst\Infrastructure\tools\artifacts\omni\canonical_uuids.json")

def load_registry_v2():
    if not REGISTRY_PATH.exists():
        print("❌ Registry not found!")
        return {}
    
    content = REGISTRY_PATH.read_text(encoding="utf-8")
    
    # Robust Frontmatter Parsing
    yaml_block = ""
    if content.startswith("---"):
        parts = content.split("---")
        if len(parts) >= 2:
            yaml_block = parts[1]
    else:
        # Assuming whole file is YAML if no separators found (legacy fallback)
        yaml_block = content
        
    try:
        data = yaml.safe_load(yaml_block)
        if not data: return {}
        
        entities = data.get("entities", [])
        return entities
    except Exception as e:
        print(f"❌ YAML Parse Error: {e}")
        return []

def load_db_dump():
    if not DB_DUMP_PATH.exists():
        print("❌ DB Dump not found")
        return {}
        
    with open(DB_DUMP_PATH, "r", encoding="utf-8") as f:
         return json.load(f)

def normalize_kind(k):
    """Normalize registry kinds to DB types (AGENT, PROJECT)."""
    k = k.lower().strip()
    if k in ["agent", "user", "persona"]: return "AGENT"
    if k in ["project", "repo", "library", "tool", "infra", "memory_system", "station", "blueprint", "foundation", "governance", "language", "mcp_server", "location", "external"]: return "PROJECT"
    return "UNKNOWN"

def build_lookup_table(entities):
    """
    Builds a Typed Lookup Table:
    lookup[KIND][SLUG] = Entity
    """
    lookup = {
        "AGENT": {},
        "PROJECT": {}
    }
    
    for e in entities:
        # Determine Kind
        raw_kind = e.get("kind", "project")
        kind = normalize_kind(raw_kind)
        
        entry = {
            "canonical_id": e.get("canonical_id"),
            "uuid": e.get("facets", {}).get("core", {}).get("id"),
            # Fallback UUIDs for legacy records
            "legacy_uuid": e.get("facets", {}).get("primary_location", {}).get("id"),
            "kind": kind,
            "raw_kind": raw_kind
        }
        
        # Determine effective UUID
        effective_uuid = entry["uuid"] or entry["legacy_uuid"]
        entry["uuid"] = str(effective_uuid).lower() if effective_uuid else None

        # Index by Canonical ID
        if entry["canonical_id"]:
            slug = entry["canonical_id"].lower()
            if slug in lookup.get(kind, {}):
                print(f"⚠️  Registry Collision in {kind}: {slug} defined twice!")
            else:
                if kind in lookup:
                    lookup[kind][slug] = entry

        # Index by Aliases
        for alias in e.get("aliases", []):
            slug = alias.lower()
            if kind in lookup:
                # We overwrite aliases if necessary, or warn? 
                # For now, Canonical ID wins, but aliases map to the entity
                if slug not in lookup[kind]:
                    lookup[kind][slug] = entry
                    
    return lookup

def compare():
    entities = load_registry_v2()
    db_data = load_db_dump()
    
    # Build Typed Registry Lookup
    reg_lookup = build_lookup_table(entities)
    
    print("-" * 120)
    print(f"{'Entity Name':<35} | {'Type':<8} | {'Status':<12} | {'Registry UUID':<36} | {'DB UUID'}")
    print("-" * 120)
    
    # Metrics
    counts = {"MATCH": 0, "DIVERGED": 0, "DB_ONLY": 0, "REG_ONLY": 0, "CONFLICT": 0}

    # Iterate DB (The Truth)
    # DB Dump keys are UUIDs, values have 'name' and 'type'
    
    # We want to iterate by NAME to find them in registry? 
    # Or iterate the DB items and look them up?
    
    # Let's iterate DB items
    for db_uuid, db_record in db_data.items():
        db_name = db_record.get("name", "Unknown")
        db_type = db_record.get("type", "PROJECT").upper() # Default to PROJECT
        
        # Normalize DB Type
        if db_type == "AGENT":
            search_kind = "AGENT"
        else:
            search_kind = "PROJECT"
            
        # Search in Registry's Typed Namespace
        # Try exact name match
        slug = db_name.lower().replace(" ", "-").replace("_", "-") 
        # Note: We normalized registry to kebab-case, so we should try to match that
        
        reg_match = reg_lookup[search_kind].get(slug)
        
        # If not found, try aliases (which are also in the lookup keys)
        if not reg_match:
             # Try raw name
             reg_match = reg_lookup[search_kind].get(db_name.lower())

        if reg_match:
            # Check UUID
            reg_uuid = reg_match["uuid"]
            db_uuid_str = str(db_uuid).lower()
            
            if reg_uuid == db_uuid_str:
                status = "MATCH"
                # print(f"{db_name[:35]:<35} | {db_type:<8} | {status:<12} | {reg_uuid:<36} | {db_uuid_str}")
                counts["MATCH"] += 1
            else:
                status = "DIVERGED"
                print(f"{db_name[:35]:<35} | {db_type:<8} | 🔴 {status:<10} | {str(reg_uuid):<36} | {db_uuid_str}")
                counts["DIVERGED"] += 1
        else:
            # DB Only (or name mismatch)
            status = "DB_ONLY"
            # print(f"{db_name[:35]:<35} | {db_type:<8} | 🔵 {status:<10} | {'-':<36} | {str(db_uuid).lower()}")
            counts["DB_ONLY"] += 1
            
    print("-" * 120)
    print(f"SUMMARY: {counts}")
    print("NOTE: 'DIVERGED' means same name/kind but different UUID.")
    print("NOTE: 'DB_ONLY' means present in DB but name not found in Registry (under that Type).")

if __name__ == "__main__":
    compare()
