"""
hydrate_registry_final.py
Description: The Council Convergence Protocol (v2.5).
             Connects to Postgres. Identifies missing Agents and Projects.
             Generates YAML addition files for the Registry.
             Respects the Dual Entity Model (No Identity Fusion).
Author: Ace + Mega + AntiGravity
"""

import sys
import psycopg2
import yaml # Using PyYAML for generation, ruamel not strictly needed for checking existence
from pathlib import Path
import sys
import os
import getpass
import psycopg2
import yaml
from pathlib import Path
import json
from dotenv import load_dotenv

# Load .env variables (if available)
load_dotenv()

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import sys
import os
import getpass
import psycopg2
import yaml
from pathlib import Path
import json

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# -------------------------------------------------------------------------
# SECURITY: Env Var Injection (No Hardcoded Secrets)
# -------------------------------------------------------------------------
DB_CONFIG = {
    "dbname": os.getenv("CMS_DB_NAME", "cms_db"),
    "user": os.getenv("CMS_DB_USER", "postgres"),
    "host": os.getenv("CMS_DB_HOST", "localhost"),
    "port": int(os.getenv("CMS_DB_PORT", "5433")),
}

def get_db_password() -> str:
    pw = os.getenv("CMS_DB_PASSWORD")
    if pw:
        return pw
    # Interactive fallback (masked input)
    print("🔐 Password required for DB connection (cached in env if possible).")
    return getpass.getpass("Postgres password (CMS_DB_PASSWORD): ")

def get_db_connection():
    # Sanity check: Ensure no inline password leaked into the static config
    if "password" in DB_CONFIG:
        raise RuntimeError("🚨 SECURITY ALERT: Inline DB password detected in source. Use CMS_DB_PASSWORD env var.")
    
    cfg = dict(DB_CONFIG)
    cfg["password"] = get_db_password()
    return psycopg2.connect(**cfg)

REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.md")

def load_registry_uuids():
    """Extracts known UUIDs from the master registry."""
    known_uuids = set()
    if not REGISTRY_PATH.exists():
        print(f"⚠️ Registry not found at {REGISTRY_PATH}")
        return known_uuids

    print(f"📖 Loading registry: {REGISTRY_PATH}")
    try:
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Robust Frontmatter Extraction
        yaml_content = ""
        if content.startswith('---'):
            parts = content.split('---')
            # [0] is empty, [1] is frontmatter, [2] is content
            if len(parts) >= 3:
                yaml_content = parts[1]
            else:
                yaml_content = content # Fallback
        else:
            # Maybe it doesn't have frontmatter?
            yaml_content = content

        data = yaml.safe_load(yaml_content)
        
        count = 0
        if data and 'entities' in data:
            for entity in data['entities']:
                count += 1
                # Extract Core UUID
                core_id = entity.get('facets', {}).get('core', {}).get('id')
                if core_id:
                    known_uuids.add(str(core_id))
                
                # Extract Agent Persona ID (Legacy or Dual)
                agent_id = entity.get('facets', {}).get('agent_persona', {}).get('id')
                if agent_id:
                    known_uuids.add(str(agent_id))
                
        print(f"   ✅ Parsed {count} existing entities")
        print(f"   ✅ Tracking {len(known_uuids)} unique UUIDs")
            
    except Exception as e:
        print(f"⚠️ Failed to parse registry YAML: {e}")
        # Continue with empty set to allow generation
    
    return known_uuids

def generate_additions():
    known_uuids = load_registry_uuids()
    
    print(f"📡 Connecting to PostgreSQL: {DB_CONFIG['dbname']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected successfully (Authenticated)")
        
        # --- AGENTS ---
        print("📊 Scanning agents table...")
        cursor.execute("SELECT id, name, kind, role FROM agents;")
        db_agents = cursor.fetchall()
        
        new_agents = []
        for row in db_agents:
            uuid, name, kind, role = row
            uuid_str = str(uuid)
            
            if uuid_str not in known_uuids:
                # Create Agent Entry
                new_agents.append({
                    "canonical_id": name.lower().replace(" ", "_").replace("-", "_"),
                    "display_name": name,
                    "kind": "agent",
                    "role": role or "Undefined Role",
                    "status": "active",
                    "facets": {
                        "core": {
                            "id": uuid_str,
                            "local_path": f"agents/{name.lower().replace(' ', '-')}"
                        },
                        "agent": {
                            "source": "db_hydration"
                        }
                    },
                    "tags": ["Infrastructure", "Hydrated"]
                })
        
        # --- PROJECTS ---
        print("📊 Scanning projects table...")
        cursor.execute("SELECT id, key, name, type, status FROM projects;")
        db_projects = cursor.fetchall()
        
        new_projects = []
        for row in db_projects:
            uuid, key, name, p_type, status = row
            uuid_str = str(uuid)
            
            # skip default project
            if uuid_str == "00000000-0000-0000-0000-000000000001":
                continue

            if uuid_str not in known_uuids:
                new_projects.append({
                    "canonical_id": key or name.lower().replace(" ", "-"),
                    "display_name": name,
                    "kind": "project",
                    "status": status or "active",
                    "facets": {
                        "core": {
                            "id": uuid_str,
                            "local_path": f"projects/{key or name}" 
                        },
                        "project": {
                            "type": p_type,
                            "source": "db_hydration"
                        },
                        "repo": {
                            "primary_repo": "" 
                        }
                    },
                    "tags": ["Hydrated"]
                })

        conn.close()

        print("💾 Writing addition files...")
        
        if new_agents:
            with open('_generated_agents_additions.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(new_agents, f, sort_keys=False)
            print(f"📝 Generated {len(new_agents)} agent(s) → _generated_agents_additions.yaml")
        else:
            print("   No new agents found.")

        if new_projects:
            with open('_generated_projects_additions.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(new_projects, f, sort_keys=False)
            print(f"📝 Generated {len(new_projects)} project(s) → _generated_projects_additions.yaml")
        else:
            print("   No new projects found.")

        print("="*64)
        print("✅ HYDRATION COMPLETE")
        print("="*64)

    except Exception as e:
        print(f"❌ DB Error: {e}")

if __name__ == "__main__":
    generate_additions()
