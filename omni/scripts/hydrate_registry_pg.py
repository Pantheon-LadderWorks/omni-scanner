"""
hydrate_registry_pg.py
Description: Connects to the Live Postgres Truth and hydrates the Registry with Canonical UUIDs.
             Respects the Agent/Project Dual Entity Model.
             Uses ruamel.yaml to preserve comments and structure.
Author: AntiGravity (via Ace's Design)
"""

import sys
import psycopg2
from ruamel.yaml import YAML
from pathlib import Path

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    "dbname": "cms_db",
    "user": "postgres",
    "password": "58913070Krdpn!!",
    "host": "localhost",
    "port": "5433"
}

REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.md")

def get_db_truth():
    print("🔌 Connecting to Postgres...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Fetch Agents
        cursor.execute("SELECT id, name FROM agents;")
        agents = {row[1]: row[0] for row in cursor.fetchall()}
        print(f"   ✅ Loaded {len(agents)} Agents")

        # 2. Fetch Projects
        # Key is often the repo name or id-slug
        cursor.execute("SELECT id, name, key FROM projects;")
        projects = {}
        for row in cursor.fetchall():
            pid, name, key = row
            projects[name] = pid
            if key:
                projects[key] = pid
        print(f"   ✅ Loaded {len(projects)} Projects (by name/key)")
        
        conn.close()
        return agents, projects
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None, None

def hydrate():
    if not REGISTRY_PATH.exists():
        print(f"❌ Registry not found: {REGISTRY_PATH}")
        return

    agents_db, projects_db = get_db_truth()
    if not agents_db:
        return

    yaml = YAML()
    yaml.preserve_quotes = True
    
    print(f"📖 Reading Registry: {REGISTRY_PATH}")
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        # Check for frontmatter
        content = f.read()
        parts = content.split('---')
        if len(parts) >= 3:
            # Has frontmatter?
            # Actually, the file seems to start with --- registry: ...
            # treated as one YAML doc by ruamel usually?
            pass

    # Re-read with ruamel
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        data = yaml.load(f)

    if 'entities' not in data:
        print("⚠️ No entities found in registry.")
        return

    updates = 0
    
    print("-" * 60)
    print(f"{'Entity':<30} | {'Kind':<10} | {'Action':<15} | {'UUID'}")
    print("-" * 60)

    for entity in data['entities']:
        name = entity.get('display_name')
        kind = entity.get('kind', 'unknown').lower()
        aliases = entity.get('aliases', [])
        
        # --- STRATEGY: DUAL ENTITY RESOLUTION ---
        
        target_uuid = None
        source = ""

        # 1. AGENT Matching
        if kind == 'agent':
            # Try matching by Display Name or Aliases in Agents DB
            if name in agents_db:
                target_uuid = agents_db[name]
                source = "DB:Agents(Name)"
            else:
                for alias in aliases:
                    if alias in agents_db:
                        target_uuid = agents_db[alias]
                        source = f"DB:Agents({alias})"
                        break
            
            # Update facets.agent_persona.id
            if target_uuid:
                facets = entity.setdefault('facets', {})
                persona = facets.setdefault('agent_persona', {})
                current_id = persona.get('id')
                
                if current_id != target_uuid:
                    persona['id'] = target_uuid
                    print(f"{name:<30} | {kind:<10} | UPDATED (A)   | {target_uuid} ({source})")
                    updates += 1
                else:
                    print(f"{name:<30} | {kind:<10} | MATCHED (A)   | {target_uuid}")

        # 2. PROJECT Matching
        elif kind == 'project':
            # Try matching by Display Name or Aliases or Canonical ID in Projects DB
            candidates = [name] + aliases + [entity.get('canonical_id')]
            
            for candidate in candidates:
                if candidate and candidate in projects_db:
                    target_uuid = projects_db[candidate]
                    source = f"DB:Projects({candidate})"
                    break
            
            # Update facets.core.id OR just top level if schema varies?
            # Usually facets.core.id for projects
            if target_uuid:
                facets = entity.setdefault('facets', {})
                core = facets.setdefault('core', {})
                current_id = core.get('id')
                
                if current_id != target_uuid:
                    core['id'] = target_uuid
                    print(f"{name:<30} | {kind:<10} | UPDATED (P)   | {target_uuid} ({source})")
                    updates += 1
                else:
                    print(f"{name:<30} | {kind:<10} | MATCHED (P)   | {target_uuid}")

        # 3. STATION / OTHER Matching
        else:
             print(f"{name:<30} | {kind:<10} | SKIPPED       | -")

    print("-" * 60)
    
    if updates > 0:
        print(f"💾 Saving {updates} updates to Registry...")
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        print("✅ Registry Hydration Complete.")
    else:
        print("✨ Registry is already fully hydrated.")

if __name__ == "__main__":
    hydrate()
