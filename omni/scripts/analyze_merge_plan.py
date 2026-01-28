"""
analyze_merge_plan.py
Description: PHASE 1 (Read-Only) - Generates a Merge Plan for Registry Identity Reconciliation.
             Identifies UUID matches, mismatched identities, and duplicate collisions.
             Output: merge_plan.json (Artifact for review).
"""

import yaml
import json
import re
from pathlib import Path

# Config
REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.remediated.md") # Use the latest remediated logic
DB_DUMP_PATH  = Path(r"C:\Users\kryst\Infrastructure\tools\artifacts\omni\canonical_uuids.json")
OUTPUT_PLAN   = Path(r"C:\Users\kryst\Infrastructure\tools\merge_plan.json")

def normalize_slug(s):
    if not s: return ""
    return str(s).strip().lower().replace("_", "-").replace(" ", "-")

def analyze():
    print(f"Loading Registry: {REGISTRY_PATH}")
    reg_content = REGISTRY_PATH.read_text(encoding="utf-8")
    reg_data = yaml.safe_load(reg_content.split("---")[1])
    entities = reg_data.get("entities", [])

    print(f"Loading DB Dump: {DB_DUMP_PATH}")
    db_data = json.load(DB_DUMP_PATH.open(encoding="utf-8"))

    # 1. Index DB
    db_by_uuid = db_data # UUID -> Record
    db_by_slug = {}      # Slug -> List of (UUID, Record)
    
    for u, rec in db_data.items():
        name = rec.get("name", "")
        slug = normalize_slug(name)
        if slug not in db_by_slug: db_by_slug[slug] = []
        db_by_slug[slug].append( (u, rec) )

    # 2. Plan Actions
    plan = {
        "valid_matches": [],
        "uuid_mismatches": [],
        "db_duplicates": [],
        "registry_collisions": [],
        "missing_in_db": []
    }

    # Registry Processing
    seen_registry_slugs = {} # slug -> cid

    for e in entities:
        cid = e.get("canonical_id")
        uuid = e.get("facets", {}).get("core", {}).get("id")
        
        # Self-Collision Check
        if cid in seen_registry_slugs:
            plan["registry_collisions"].append({
                "collision": cid,
                "entity_a": seen_registry_slugs[cid],
                "entity_b": e.get("display_name", "UNKNOWN")
            })
        seen_registry_slugs[cid] = e.get("display_name", cid)
        
        # Alias Collision Check (Scribes case)
        for a in e.get("aliases", []):
            aslug = normalize_slug(a)
            if aslug in seen_registry_slugs and aslug != cid:
                 plan["registry_collisions"].append({
                    "collision_type": "Alias vs Canonical",
                    "slug": aslug,
                    "owner_canonical": seen_registry_slugs[aslug],
                    "offender_alias_in": cid
                })

        # Match Logic
        match_found = False
        
        # A. UUID Match
        if uuid:
            norm_uuid = str(uuid).lower()
            if norm_uuid in db_by_uuid:
                plan["valid_matches"].append({"cid": cid, "uuid": norm_uuid, "db_name": db_by_uuid[norm_uuid]["name"]})
                match_found = True
            else:
                 plan["missing_in_db"].append({"cid": cid, "uuid": uuid, "status": "UUID_NOT_IN_DB"})
        
        # B. Slug Match (if no UUID match confirmed yet or to check drift)
        slug = normalize_slug(cid)
        if slug in db_by_slug:
            duplicates = db_by_slug[slug]
            if len(duplicates) > 1:
                plan["db_duplicates"].append({
                    "cid": cid, 
                    "db_matches": [{"uuid": u, "name": r["name"]} for u, r in duplicates]
                })
            elif not match_found:
                # Found by slug, but UUID didn't match (or wasn't present)
                u, r = duplicates[0]
                if uuid and str(uuid).lower() != str(u).lower():
                     plan["uuid_mismatches"].append({
                         "cid": cid,
                         "registry_uuid": uuid,
                         "db_uuid": u,
                         "db_name": r["name"]
                     })

    # Save Plan
    OUTPUT_PLAN.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"✅ Plan Generated: {OUTPUT_PLAN}")
    print(f"Summary:")
    print(f"  Matches: {len(plan['valid_matches'])}")
    print(f"  UUID Mismatches: {len(plan['uuid_mismatches'])}")
    print(f"  DB Duplicates: {len(plan['db_duplicates'])}")
    print(f"  Registry Collisions: {len(plan['registry_collisions'])}")

if __name__ == "__main__":
    analyze()
