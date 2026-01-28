"""
refactor_registry_safe.py
Description: Safely refactors PROJECT_REGISTRY_MASTER.md to Schema v2.1.
             Merges 'projects' list into 'entities', normalizes IDs/Tags, and enforces strict Safe Merge rules.
             Adopts Option A: Global Namespace (kebab-case).
             Includes Mega's safety patches (Hardened tags, No None IDs, Kind Check, Out-of-place write).
             Includes Split Logic for atlas-forge, seraphina.
             Includes Kind Upcasting (Project -> Tool/Memory/Agent).
"""

import yaml
import re
from pathlib import Path
import copy

# Read from BACKUP to ensure we have the legacy 'projects' list
REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.bak.md")
OUTPUT_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.refactored.md")

# --- CANONICAL SPLITS ---
CANON_SPLITS = {
    "atlas-forge": {"tool": "atlas-forge-tool", "project": "atlas-forge"},
    "seraphina": {"agent": "seraphina", "project": "seraphina-core"},
}

# --- UTILS ---

def normalize_slug(s):
    if not s: return None
    normalized = str(s).strip().lower().replace("_", "-").replace(" ", "-")
    return normalized if normalized else None

def normalize_tags(tags):
    if not tags: return []
    if isinstance(tags, str): tags = [tags]
    final = []
    for t in tags:
        if not t: continue
        t = str(t).strip()
        if not t: continue
        if "," in t:
            final.extend([p.strip() for p in t.split(",") if p.strip()])
        else:
            final.append(t)
    return sorted(list(set(final)))

def deep_merge(target, source):
    for key, val in source.items():
        if key in target:
            if isinstance(target[key], dict) and isinstance(val, dict):
                deep_merge(target[key], val)
            elif isinstance(target[key], list) and isinstance(val, list):
                combined = target[key] + [x for x in val if x not in target[key]]
                target[key] = combined
            else:
                if not target[key] and val:
                    target[key] = val
        else:
            target[key] = val
    return target

# --- CONVERTERS ---

def convert_project_item_to_entity(p):
    slug = normalize_slug(p.get("project_id"))
    entity = {
        "canonical_id": slug,
        "display_name": p.get("display_name", slug),
        "kind": p.get("kind", "project"),
        "status": p.get("status", "active"),
        "tags": normalize_tags(p.get("tags", [])),
        "aliases": [],
        "facets": {}
    }
    facets = entity["facets"]
    if "repo" in p:
        url = p["repo"].get("url")
        if url:
            if "repo" not in facets: facets["repo"] = {}
            facets["repo"]["primary_repo"] = url
    lpaths = p.get("local_paths", [])
    if lpaths:
         if "repo" not in facets: facets["repo"] = {}
         facets["repo"]["local_paths"] = lpaths
    return entity

# --- SAFETY ---

def is_safe_merge(e1, e2):
    id1 = e1.get("facets", {}).get("core", {}).get("id")
    id2 = e2.get("facets", {}).get("core", {}).get("id")
    if id1 and id2 and str(id1).strip() != str(id2).strip():
        return False, f"UUID Conflict: {id1} vs {id2}"
    
    k1 = (e1.get("kind") or "").strip().lower()
    k2 = (e2.get("kind") or "").strip().lower()
    
    if k1 and k2 and k1 != k2:
        specific_kinds = {"tool", "memory_system", "agent", "governance", "language", "mcp_server", "station", "blueprint", "foundation", "location", "orchestration"}
        if k1 in specific_kinds and k2 == "project":
            return True, f"Upcast OK ({k2}->{k1})"
        if k1 == "project" and k2 in specific_kinds:
            return True, f"Upcast OK ({k1}->{k2})"
        return False, f"Kind Conflict: {k1} vs {k2}"
    return True, "OK"

def apply_split_rules(item, kind):
    cid = item["canonical_id"]
    if cid in CANON_SPLITS:
        mapping = CANON_SPLITS[cid]
        if kind in mapping:
            item["canonical_id"] = mapping[kind]
            return
        if "project" in mapping and kind == "project":
             item["canonical_id"] = mapping["project"]
             return

# --- MAIN ---

def refactor():
    if not REGISTRY_PATH.exists():
        print("❌ Registry path not found.")
        return

    content = REGISTRY_PATH.read_text(encoding="utf-8")
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, flags=re.S)
    if not match:
        print("❌ Could not extract Frontmatter via Regex.")
        return

    frontmatter_raw = match.group(1)
    markdown_body = content[match.end():]

    try:
        data = yaml.safe_load(frontmatter_raw)
    except Exception as e:
        print(f"❌ YAML Error: {e}")
        return

    raw_entities = data.get("entities", [])
    raw_projects = data.get("projects", [])
    
    print(f"INPUT: {len(raw_entities)} Entities, {len(raw_projects)} Projects.")

    merged_registry = {}

    for e in raw_entities:
        cid = normalize_slug(e.get("canonical_id"))
        if not cid: continue
        e["canonical_id"] = cid
        e["tags"] = normalize_tags(e.get("tags", []))
        if "facets" not in e: e["facets"] = {}
        
        apply_split_rules(e, e.get("kind", "project"))
        cid = e["canonical_id"]
        
        if cid in merged_registry:
            safe, msg = is_safe_merge(merged_registry[cid], e)
            if not safe:
                print(f"   ❌ UNSAFE MERGE SKIPPED (Base): {cid} - {msg}")
                continue
            deep_merge(merged_registry[cid], e)
        else:
            merged_registry[cid] = e

    for p in raw_projects:
        raw_slug = p.get("project_id")
        if not raw_slug: continue
        entity = convert_project_item_to_entity(p)
        apply_split_rules(entity, "project")
        cid = entity["canonical_id"]
        if not cid: continue

        if cid == "federation-station":
            url = entity.get("facets", {}).get("repo", {}).get("primary_repo", "")
            if "Pantheon-LadderWorks" in url: cid = "cloud-federation-station"
            else: cid = "federation-space"
            entity["canonical_id"] = cid
            
        if cid == "ghost-finger-manager": pass
            
        if cid in merged_registry:
            existing = merged_registry[cid]
            safe, msg = is_safe_merge(existing, entity)
            if safe:
                k1 = existing.get("kind", "project")
                k2 = entity.get("kind", "project")
                specific_kinds = {"tool", "memory_system", "agent", "governance", "language", "mcp_server", "station", "blueprint", "foundation", "location", "orchestration"}
                if k1 in specific_kinds and k2 == "project":
                    entity["kind"] = k1 
                elif k1 == "project" and k2 in specific_kinds:
                    existing["kind"] = k2
                deep_merge(existing, entity)
                print(f"   Merged Project -> Entity: {cid} ({msg})")
            else:
                print(f"   ❌ UNSAFE MERGE (Project->Entity): {cid} - {msg}")
        else:
            merged_registry[cid] = entity
            print(f"   Promoted Project -> Entity: {cid}")

    final_list = list(merged_registry.values())
    final_list.sort(key=lambda x: x["canonical_id"])
    
    data["entities"] = final_list
    if "projects" in data: del data["projects"]

    new_yaml = yaml.dump(data, sort_keys=False, width=1000)
    
    clean_md = markdown_body
    for h in ["# --- HYDRATED", "# 2. Projects (Repositories)", "# 3. Locations"]:
        parts = clean_md.split(h)
        if len(parts) > 1: clean_md = parts[0]
            
    output = "---\n" + new_yaml + "---\n\n" + clean_md.strip() + "\n"
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"✅ Safe Refactor Complete. Written to: {OUTPUT_PATH}")
    print(f"   Total Entities: {len(final_list)}")

if __name__ == "__main__":
    refactor()
