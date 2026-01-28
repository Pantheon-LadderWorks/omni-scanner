"""
Universal UUID Wiring - Trinity Pattern Enforcer
================================================

Synchronizes UUIDs across the Trinity of Truth:
1. Database (canonical_uuids.json) -> SOURCE OF TRUTH (Base)
2. Council Registry (COUNCIL_UUID_REGISTRY.yaml) -> PRIORITY SOURCE (Council Agents)
3. Formation Registry (COUNCIL_FORMATION_REGISTRY.yaml) -> PRIORITY SOURCE (Formations)
4. Registry (PROJECT_REGISTRY_MASTER.md) -> INDEX (To be updated later)
5. File System (package.json, agent.py, README.md, test_*.py) -> REALITY

"""
import json
import yaml # PyYAML fallback
import re
from pathlib import Path
import uuid as uuid_lib

# Paths
INFRA_ROOT = Path("C:/Users/kryst/Infrastructure")
# Absolute path to artifacts if running from tools/
DB_DUMP_PATH = INFRA_ROOT / "tools/artifacts/omni/canonical_uuids.json"
REGISTRY_PATH = INFRA_ROOT / "PROJECT_REGISTRY_MASTER.md"
COUNCIL_REGISTRY_PATH = INFRA_ROOT / "agents/COUNCIL_UUID_REGISTRY.yaml"
COUNCIL_FORMATION_REGISTRY_PATH = INFRA_ROOT / "agents/agent-tools/council-formation-tests/COUNCIL_FORMATION_REGISTRY.yaml"

def ensure_formation_uuids_ruamel():
    """Use ruamel.yaml to preserve comments while updating missing UUIDs."""
    try:
        from ruamel.yaml import YAML
        ryaml = YAML()
        ryaml.preserve_quotes = True
        ryaml.width = 4096 # Avoid wrap
        
        if not COUNCIL_FORMATION_REGISTRY_PATH.exists():
             return {}

        content = COUNCIL_FORMATION_REGISTRY_PATH.read_text(encoding='utf-8')
        data = ryaml.load(content)
        mapping = {}
        updates = False
        
        if 'formations' in data:
            for key, formation in data['formations'].items():
                if 'formation_uuid' not in formation:
                    new_uuid = str(uuid_lib.uuid4())
                    # Insert at top (index 1 after id/key usually) or 0
                    formation.insert(0, 'formation_uuid', new_uuid) 
                    updates = True
                    print(f"  [Registry] Generated UUID for {key}: {new_uuid}")
                
                uuid = formation['formation_uuid']
                mapping[key] = uuid
                if 'formation_name' in formation:
                    mapping[formation['formation_name']] = uuid
        
        if updates:
            # We must be careful. ruamel might change formatting slightly.
            # But preserving comments is its superpower.
            with open(COUNCIL_FORMATION_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                ryaml.dump(data, f)
            print("  [Registry] Updated COUNCIL_FORMATION_REGISTRY.yaml with new UUIDs.")
            
        return mapping
    except Exception as e:
        print(f"ERROR with ruamel.yaml: {e}")
        # Fallback to empty
        return {}

def load_db_uuids():
    """Load UUIDs from the DB dump (Dict of UUID -> Object)."""
    if not DB_DUMP_PATH.exists():
        print(f"ERROR: DB Dump not found at {DB_DUMP_PATH}")
        return {}
    
    try:
        with open(DB_DUMP_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Structure: { "uuid": { "name": "...", ... } }
            if isinstance(data, dict):
                # Map Name -> UUID (Key)
                # Filter out entries without name?
                mapping = {}
                for uuid, meta in data.items():
                    name = meta.get('name')
                    if name:
                        mapping[name] = uuid
                return mapping
            elif isinstance(data, list):
                # Old assumptions
                return {item['name']: item['id'] for item in data}
            else:
                 print(f"ERROR: DB Dump Unknown Format: {type(data)}")
                 return {}
    except Exception as e:
        print(f"ERROR Loading DB Dump: {e}")
        return {}

def load_council_registry():
    """Load UUIDs from the Council UUID Registry YAML."""
    if not COUNCIL_REGISTRY_PATH.exists():
        return {}
    
    try:
        content = COUNCIL_REGISTRY_PATH.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        mapping = {}
        
        # Parse Agents
        if 'agents' in data:
            for agent in data['agents']:
                name = agent.get('display_name')
                key = agent.get('key')
                # Prioritize cmp_agent_id, fallback to static_uuid
                uuid = agent.get('cmp_agent_id') or agent.get('static_uuid')
                
                if uuid:
                     if name: mapping[name] = uuid
                     # Helper aliases
                     if key == "ACE": mapping["ace-agent"] = uuid
                     if key == "MEGA": mapping["mega-agent"] = uuid
                     if key == "ORACLE": mapping["oracle-agent"] = uuid
                     if key == "SERAPHINA_SHELL": mapping["seraphina-shell"] = uuid 
        
        # Parse Tools
        if 'tools' in data:
            for tool in data['tools']:
                 name = tool.get('display_name')
                 uuid = tool.get('static_uuid')
                 if name and uuid:
                     mapping[name] = uuid
        
        return mapping
    except Exception as e:
        print(f"ERROR Loading Council Registry: {e}")
        return {}

def load_formation_registry():
    """Load Formation UUIDs from the Formation Registry YAML."""
    if not COUNCIL_FORMATION_REGISTRY_PATH.exists():
        return {}

    try:
        content = COUNCIL_FORMATION_REGISTRY_PATH.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        mapping = {}
        
        if 'formations' in data:
            # formations is a dict of keys -> formation dict
            for key, formation in data['formations'].items():
                name = formation.get('formation_name')
                uuid = formation.get('formation_uuid') # This key MUST exist per audit
                
                if uuid:
                    mapping[key] = uuid # Map 'mind_forge' -> uuid
                    if name: mapping[name] = uuid

        return mapping
    except Exception as e:
        print(f"ERROR Loading Formation Registry: {e}")
        return {}

def load_registry_map():
    """Parse Registry YAML to get current UUID map and file location."""
    if not REGISTRY_PATH.exists():
        return {}
    
    content = REGISTRY_PATH.read_text(encoding='utf-8')
    
    # Robust Frontmatter Extraction
    yaml_block = content
    if content.startswith("---\n"):
        parts = content[4:].split("\n---\n")
        if len(parts) > 0:
            yaml_block = parts[0]
    else:
        parts = content.split("\n---\n")
        if len(parts) > 0:
            yaml_block = parts[0]

    try:
        data = yaml.safe_load(yaml_block)
        entities = data.get('entities', [])
        reg_map = {}
        for e in entities:
            # Use 'canonical_id' or 'display_name' or 'aliases'
            # We map Display Name -> UUID
            name = e.get('display_name')
            aliases = e.get('aliases', [])
            
            uuid = None
            path = None
            
            # Extract UUID from facets
            facets = e.get('facets', {})
            if 'core' in facets:
                uuid = facets['core'].get('id')
                path = facets['core'].get('local_path')
            elif 'agent_persona' in facets:
                uuid = facets['agent_persona'].get('id')
                path = facets['agent_persona'].get('local_path')
            elif 'primary_location' in facets:
                uuid = facets['primary_location'].get('type_id') # Rare?
                # Usually missing id here
                path = facets['primary_location'].get('local_path')
            elif 'station_core' in facets:
                uuid = facets['station_core'].get('id')
                path = facets['station_core'].get('local_path')
            
            if name:
                reg_map[name] = {"uuid": uuid, "path": path}
            
            # Map aliases too?
            for a in aliases:
                if a not in reg_map:
                    reg_map[a] = {"uuid": uuid, "path": path}

        return reg_map
    except Exception as e:
        print(f"Registry Parse Error: {e}")
        return {}

def wire_package_json(project_path, uuid):
    pkg_json = project_path / "package.json"
    if pkg_json.exists():
        content = pkg_json.read_text(encoding='utf-8')
        if '"uuid":' not in content:
            new_content = re.sub(r'("version": ".*?",)', f'\\1\n  "uuid": "{uuid}",', content)
            if new_content != content:
                pkg_json.write_text(new_content, encoding='utf-8')
                print(f"  [Config] Wired package.json in {project_path.name}")
        # else check mismatch?
        elif uuid not in content:
             print(f"  [Config] MISMATCH in package.json: {project_path.name}")

def wire_readme(project_path, uuid):
    readme = project_path / "README.md"
    if readme.exists():
        content = readme.read_text(encoding='utf-8')
        if uuid not in content:
            badge = f"![UUID](https://img.shields.io/badge/UUID-{uuid}-blue)"
            lines = content.split('\n')
            inserted = False
            for i, line in enumerate(lines):
                if line.startswith("# "):
                    lines.insert(i+2, badge)
                    inserted = True
                    break
            if not inserted:
                lines.insert(0, badge)
            readme.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  [Docs] Wired README.md in {project_path.name}")

def wire_python_agent(project_path, uuid, agent_name):
    agent_py = project_path / "src/agent.py"
    if not agent_py.exists():
        return 

    content = agent_py.read_text(encoding='utf-8')
    
    # Regex to find existing AGENT_ID
    # Pattern: AGENT_ID = "..." (Capture the UUID)
    agent_id_pattern = r'AGENT_ID\s*=\s*"([^"]+)"'
    match = re.search(agent_id_pattern, content)
    
    if match:
        existing_uuid = match.group(1)
        if existing_uuid != uuid:
            print(f"  [Code] FIXING Mismatch in {project_path.name}: {existing_uuid} -> {uuid}")
            new_content = re.sub(agent_id_pattern, f'AGENT_ID = "{uuid}"', content)
            # Re-write the file
            agent_py.write_text(new_content, encoding='utf-8')
        return

    # If not found, inject block
    match_imp = re.search(r'(""".*?"""\n\n)(from|import)', content, re.DOTALL)
    if match_imp:
        docstring_end = match_imp.start(2)
        constants_block = f"""
# ═══════════════════════════════════════════════════════════════════════
# UUID TRINITY ANCHOR POINT #3 (RUNTIME BRAIN)
# ═══════════════════════════════════════════════════════════════════════
AGENT_ID = "{uuid}"
AGENT_NAME = "{agent_name}"
CMP_SOURCE = "cmp://agents/{uuid}"
# ═══════════════════════════════════════════════════════════════════════

"""
        new_content = content[:docstring_end] + constants_block + content[docstring_end:]
        agent_py.write_text(new_content, encoding='utf-8')
        print(f"  [Code] Wired agent.py in {project_path.name}")

def wire_formation_file(uuid, formation_key, infra_root):
    formation_root = infra_root / "agents/agent-tools/council-formation-tests"
    if not formation_root.exists():
        return

    search_patterns = [
        f"test_{formation_key}.py",
        f"test_{formation_key}_axis.py", # dyads
        f"test_triad_{formation_key}.py", # triads
        f"test_triad_{formation_key.lower()}.py",
        f"test_octad_{formation_key}.py"
    ]
    
    # Specific map for A1, T2 etc if needed
    # A1 -> test_triad_execution_core.py
    # But wait, formation_key is usually 'A1' or 'mind_forge'.
    # If key is 'A1', we need to map to 'execution_core'??
    # No, let's rely on formation_name or just assume keys match filenames somewhat.
    # Actually, the user's registry has specific test files.
    # wire_uuid_universal doesn't know them unless I hardcode map or logic.
    # I'll rely on pattern matching for now.
    
    # Brute force scan?
    # List all py files in subdirs
    for subdir in ['dyads', 'triads', 'octad']:
        d = formation_root / subdir
        if d.exists():
            for f in d.glob("test_*.py"):
                # Check if file matches key roughly?
                # Logic: formation_key 'mind_forge' in 'test_mind_forge_axis.py'
                if formation_key.lower() in f.name.lower():
                     content = f.read_text(encoding='utf-8')
                     if 'FORMATION_UUID =' not in content:
                         block = f"\n# TRINITY ANCHOR\nFORMATION_UUID = \"{uuid}\"\n"
                         # Insert logic
                         lines = content.split('\n')
                         last_imp = 0
                         for i, l in enumerate(lines):
                             if l.startswith('import ') or l.startswith('from '):
                                 last_imp = i
                         lines.insert(last_imp + 2, block)
                         f.write_text('\n'.join(lines), encoding='utf-8')
                         print(f"  [Formation] Wired {f.name} with {uuid}")
                         return

def main():
    print("Initializing Universal UUID Wiring (V3)...")
    db_map = load_db_uuids()
    council_map = load_council_registry()
    
    # NEW: Ensure formations have UUIDs by checking/updating the file
    formation_map = ensure_formation_uuids_ruamel() 
    
    # Merge: Council > DB
    universal_map = db_map.copy()
    universal_map.update(council_map)
    # We maintain formation_map separate for specific wiring logic
    
    reg_map = load_registry_map()
    
    print(f"Loaded {len(db_map)} DB UUIDs, {len(council_map)} Council UUIDs, {len(formation_map)} Formation UUIDs.")
    print(f"Total Unique Targets: {len(universal_map) + len(formation_map)}") 
    
    wired_count = 0
    
    # 1. Wire Projects/Agents
    for name, canonical_uuid in universal_map.items():
        if name in formation_map: continue

        target_entry = reg_map.get(name) # Try Display Name
        
        # Fallback to key? 
        if not target_entry and name.endswith("-agent"):
            # Try name without -agent?
            pass

        if target_entry:
            reg_uuid = target_entry.get('uuid')
            if not reg_uuid or reg_uuid != canonical_uuid:
                print(f"[TARGET] {name} | Truth: {canonical_uuid} | Reg: {reg_uuid}")
                path_str = target_entry.get('path')
                if path_str:
                    full_path = INFRA_ROOT / path_str
                    if full_path.exists():
                        wire_package_json(full_path, canonical_uuid)
                        wire_readme(full_path, canonical_uuid)
                        wire_python_agent(full_path, canonical_uuid, name)
                        wired_count += 1

    # 2. Wire Formations
    for key, uuid in formation_map.items():
        # key might be 'mind_forge' or 'Mind-Forge Axis'
        # Filter for keys that look like identifiers
        if ' ' not in key: 
            wire_formation_file(uuid, key, INFRA_ROOT)
            wired_count += 1
            
    print(f"Wiring Complete. Touched {wired_count} entities.")

if __name__ == "__main__":
    main()
