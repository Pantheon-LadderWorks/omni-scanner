"""
Sync Registry UUIDs
===================
Updates PROJECT_REGISTRY_MASTER.md to match the Universal Truth (DB + Council + Formations).
Replaces "Ghost IDs" with Canonical UUIDs while preserving file structure.
"""
import re
from pathlib import Path
import yaml
import json

# Reuse logic from wire_uuid_universal ideally, but for now copying the loader logic for speed/independence
# Paths
INFRA_ROOT = Path("C:/Users/kryst/Infrastructure")
DB_DUMP_PATH = INFRA_ROOT / "tools/artifacts/omni/canonical_uuids.json"
REGISTRY_PATH = INFRA_ROOT / "PROJECT_REGISTRY_MASTER.md"
COUNCIL_REGISTRY_PATH = INFRA_ROOT / "agents/COUNCIL_UUID_REGISTRY.yaml"
COUNCIL_FORMATION_REGISTRY_PATH = INFRA_ROOT / "agents/agent-tools/council-formation-tests/COUNCIL_FORMATION_REGISTRY.yaml"

def load_db_uuids():
    if not DB_DUMP_PATH.exists(): return {}
    try:
        with open(DB_DUMP_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                mapping = {}
                for uuid, meta in data.items():
                    name = meta.get('name')
                    if name: mapping[name] = uuid
                return mapping
            return {}
    except: return {}

def load_council_registry():
    if not COUNCIL_REGISTRY_PATH.exists(): return {}
    try:
        content = COUNCIL_REGISTRY_PATH.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        mapping = {}
        if 'agents' in data:
            for agent in data['agents']:
                name = agent.get('display_name')
                key = agent.get('key')
                uuid = agent.get('cmp_agent_id') or agent.get('static_uuid')
                if uuid:
                     if name: mapping[name] = uuid
                     if key == "ACE": mapping["ace-agent"] = uuid
                     if key == "MEGA": mapping["mega-agent"] = uuid
                     if key == "ORACLE": mapping["oracle-agent"] = uuid
                     if key == "SERAPHINA_SHELL": mapping["seraphina-shell"] = uuid 
        if 'tools' in data:
            for tool in data['tools']:
                 name = tool.get('display_name')
                 uuid = tool.get('static_uuid')
                 if name and uuid: mapping[name] = uuid
        return mapping
    except: return {}

def load_formation_registry():
    if not COUNCIL_FORMATION_REGISTRY_PATH.exists(): return {}
    try:
        content = COUNCIL_FORMATION_REGISTRY_PATH.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        mapping = {}
        if 'formations' in data:
            for key, formation in data['formations'].items():
                # Formations in Registry might be named "Mind-Forge Axis" or "mind_forge"
                # We need to map likely Registry display names
                uuid = formation.get('formation_uuid')
                name = formation.get('formation_name')
                if uuid:
                    if name: mapping[name] = uuid
                    mapping[key] = uuid
                    # Also map "Mind Forge" -> uuid if needed?
        return mapping
    except: return {}

def main():
    print("Initializing Registry Sync...")
    
    # 1. Load Truth
    db_map = load_db_uuids()
    council_map = load_council_registry()
    formation_map = load_formation_registry()
    
    universal_map = db_map.copy()
    universal_map.update(council_map)
    universal_map.update(formation_map)
    
    print(f"Loaded {len(universal_map)} Canonical Entities.")

    if not REGISTRY_PATH.exists():
        print("Registry not found!")
        return

    content = REGISTRY_PATH.read_text(encoding='utf-8')
    original_content = content
    
    # 2. Iterate and Replace
    # We look for patterns like:
    # - canonical_id: ...
    #   display_name: Claude
    #   ...
    #     core:
    #       id: <OLD_UUID>
    
    # Or:
    #   agent_persona:
    #      id: <OLD_UUID>
    
    # Strategy:
    # Parse the text linearly? No, regex replacement is risky if names are duplicates.
    # But usually display_name is unique enough nearby.
    
    # Better Strategy:
    # Scan the YAML frontmatter for entities.
    # If entity['display_name'] in universal_map:
    #    target_uuid = universal_map[name]
    #    current_uuid = entity.facets...id
    #    if diff: replace current_uuid with target_uuid IN THE TEXT
    
    # We need to extract the UUID from the text carefully to replace only that instance.
    
    updates = 0
    
    try:
        # Load YAML to find logic matches (Don't modify this object, just use for lookup)
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            print("No frontmatter found!")
            return
            
        yaml_text = frontmatter_match.group(1)
        data = yaml.safe_load(yaml_text)
        
        entities = data.get('entities', [])
        
        for e in entities:
             name = e.get('display_name')
             # Also try aliases
             aliases = e.get('aliases', [])
             
             canonical_uuid = universal_map.get(name)
             if not canonical_uuid:
                 # Try aliases
                 for a in aliases:
                     canonical_uuid = universal_map.get(a)
                     if canonical_uuid: break
             
             if canonical_uuid:
                 # Find where this entity is in the text?
                 # We have the entity object `e`.
                 # Find its current ID.
                 current_id = None
                 facets = e.get('facets', {})
                 for ftype in ['core', 'agent_persona', 'station_core', 'primary_location']:
                     if ftype in facets and isinstance(facets[ftype], dict):
                         if 'id' in facets[ftype]:
                             current_id = facets[ftype]['id']
                             break
                 
                 if current_id and current_id != canonical_uuid:
                     print(f"[Mismatch] {name}: {current_id} -> {canonical_uuid}")
                     # Replace ONLY this occurence if possible.
                     # Since UUIDs are unique (mostly), replacing the UUID string globally *might* be safe
                     # BUT if the old UUID is used elsewhere as a reference, we WANT to update it too.
                     # So valid strategy: Global replace of Old UUID -> New UUID.
                     
                     if current_id in content:
                         content = content.replace(current_id, canonical_uuid)
                         updates += 1
                     else:
                         print(f"  Warning: Could not find string {current_id} in text.")
    
    except Exception as ex:
        print(f"Error parsing regex/yaml: {ex}")

    if updates > 0:
        REGISTRY_PATH.write_text(content, encoding='utf-8')
        print(f"SUCCESS: Updated {updates} entities in PROJECT_REGISTRY_MASTER.md")
    else:
        print("No updates needed.")

if __name__ == "__main__":
    main()
