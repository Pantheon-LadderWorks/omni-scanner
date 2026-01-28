"""
refactor_registry.py
Description: Cleans, merges, and normalizes the PROJECT_REGISTRY_MASTER.md file.
             Fixes duplicate IDs, mixed slug styles (kebab-case), and structure issues.
             Merges the recently appended hydration blocks into the main Frontmatter.
"""

import yaml
from pathlib import Path
import re

REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.md")

def normalize_slug(s):
    if not s: return s
    # Convert underscores to hyphens, lowercase
    return s.lower().replace("_", "-").replace(" ", "-")

def normalize_tags(tags):
    if isinstance(tags, str):
        # Convert "Tag1, Tag2" string to list
        return [t.strip() for t in tags.split(",") if t.strip()]
    return tags

def refactor():
    if not REGISTRY_PATH.exists():
        print("Registry not found!")
        return

    content = REGISTRY_PATH.read_text(encoding="utf-8")
    
    # 1. Regex Extraction of Frontmatter
    import re
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, flags=re.S)
    if not match:
        print("❌ Could not extract Frontmatter with Regex.")
        return

    frontmatter_raw = match.group(1)
    markdown_body = content[match.end():]

    try:
        data = yaml.safe_load(frontmatter_raw)
    except Exception as e:
        print(f"❌ YAML Error: {e}")
        return

    entities = data.get("entities", [])
    projects_section = data.get("projects", [])
    
    print(f"ROOT: Found {len(entities)} base entities.")
    print(f"ROOT: Found {len(projects_section)} separate projects.")

    # 2. Extract Hydrated Blocks (if any remained in markdown - though we likely cleaned them last time)
    # But wait, the file view showed 'projects:' key in the YAML part? 
    # Or was it appended? 
    # My previous refactor merged hydration, but I might have missed the existing 'projects:' key 
    # if it was inside the yaml block already.
    # We will treat 'projects' list as a source to be merged into entities.

    final_entities = []
    seen_ids = {} # map id -> entity (for merging)

    def process_item(item, kind_override=None):
        # Determine ID
        old_id = item.get("canonical_id") or item.get("project_id")
        if not old_id: return

        # Normalize ID
        new_id = normalize_slug(old_id)
        
        # Determine Kind
        kind = kind_override or item.get("kind", "project")
        
        # Special Fixes
        if new_id == "federation-station":
            # Check repo to decide identity
            repo = item.get("repo", {}).get("url") or item.get("repo", {}).get("primary_repo", "")
            if "Pantheon-LadderWorks" in repo:
                new_id = "cloud-federation-station"
            else:
                new_id = "federation-space" # Rename local
                
        if new_id == "ghost-finger-manager":
           # There were duplicates here. We'll let them merge.
           pass

        item["canonical_id"] = new_id
        if "project_id" in item: del item["project_id"]
        
        item["kind"] = kind
        item["tags"] = normalize_tags(item.get("tags", []))
        
        # Merge Facets/Fields
        if new_id in seen_ids:
            existing = seen_ids[new_id]
            
            # Merge Facets
            e_facets = existing.setdefault("facets", {})
            n_facets = item.get("facets", {})
            
            # If item has direct 'repo' or 'local_paths', upgrade to facet 
            if "repo" in item and "url" in item["repo"]:
                # Convert old repo format to facet
                if "repo" not in e_facets: e_facets["repo"] = {}
                e_facets["repo"]["primary_repo"] = item["repo"]["url"]
            
            for key, val in n_facets.items():
                if key not in e_facets:
                    e_facets[key] = val
                else:
                    # Merge inner dictionaries
                    if isinstance(val, dict) and isinstance(e_facets[key], dict):
                        e_facets[key].update(val)
            
            # Merge Local Paths (Deduping)
            # ... logic to merge lists if needed
            
            print(f"   Merged {new_id}")
        else:
            seen_ids[new_id] = item
            final_entities.append(item)

    # Process Entities
    for e in entities:
        process_item(e)
        
    # Process "Projects" List (convert to kind=project entities)
    for p in projects_section:
        process_item(p, kind_override="project")

    # 3. Final Sort
    final_entities.sort(key=lambda x: x.get("canonical_id", ""))
    
    # 4. Reconstruct Data
    new_data = {
        "registry": data.get("registry", {}),
        "entities": final_entities
        # "projects": [] # Removed
    }
    
    # Dump
    new_yaml = yaml.dump(new_data, sort_keys=False, width=1000)
    
    output = "---\n" + new_yaml + "---\n\n"
    
    # Clean Markdown body (remove any left over 'projects' tables if generated)
    # We'll just keep the original descriptive text
    
    # Just truncate after the frontmatter for safety if we are replacing the whole SOT
    # But user might have text.
    # For now, let's keep the markdown body as is, assuming it was description.
    # But if the previous Hydration appended headers were still there...
    
    # Clean known hydration headers from markdown body
    clean_md = markdown_body
    for header in ["# --- HYDRATED", "# 2. Projects (Repositories)", "# 3. Locations"]:
         if header in clean_md:
             clean_md = clean_md.split(header)[0]
             
    output += clean_md.strip() + "\n"
    
    REGISTRY_PATH.write_text(output, encoding="utf-8")
    print(f"✅ Registry Refactored. Total Entities: {len(final_entities)}")

if __name__ == "__main__":
    refactor()
