"""
Canonical UUID Fetcher (Postgres)
Migrated from tools/fetch_canonical_uuids.py
"""
import os
import json
import psycopg2
from typing import Dict, List

# Connection settings
# Load .env ONLY when fetch_canonical_uuids() is called
from pathlib import Path

# Paths
CMP_PATH = Path(r"C:\Users\kryst\Infrastructure\conversation-memory-project")
CMP_ENV_PATH = CMP_PATH / ".env"

# Lazy .env loading - only happens inside fetch_canonical_uuids()
_ENV_LOADED = False

def _ensure_env_loaded():
    """Load CMP .env only when actually needed for DB operations."""
    global _ENV_LOADED
    if not _ENV_LOADED:
        try:
            from dotenv import load_dotenv
            if CMP_ENV_PATH.exists():
                load_dotenv(CMP_ENV_PATH)
                # Removed DEBUG print - no noise unless scanning CMP
            _ENV_LOADED = True
        except ImportError:
            pass  # dotenv optional

def _get_db_config():
    """Get DB config after ensuring env is loaded."""
    _ensure_env_loaded()
    return {
        "dbname": os.getenv("POSTGRES_DB", "cms_db"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "password"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5433")
    }

def fetch_canonical_uuids() -> Dict[str, Dict]:
    """Fetch UUIDs from CMP database. Loads .env on first call."""
    DB_CONFIG = _get_db_config()  # Lazy load env
    print(f"Connecting to CMS Database at {DB_CONFIG['host']}:{DB_CONFIG['port']} as {DB_CONFIG['user']}...")
    # print(f"DEBUG: Password len: {len(DB_CONFIG['password'])}")
    conn = None
    canonical_data = {}
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Fetch Agents
        print("Fetching Agents...")
        cur.execute("SELECT id, name, role, metadata_ FROM agents")
        agents = cur.fetchall()
        for row in agents:
            uuid_str = str(row[0]).lower()
            canonical_data[uuid_str] = {
                "type": "AGENT",
                "name": row[1],
                "role": row[2],
                "metadata": row[3],
                "source": "DB:agents"
            }
            
        # 2. Fetch Projects
        print("Fetching Projects...")
        cur.execute("SELECT id, name FROM projects")
        projects = cur.fetchall()
        for row in projects:
            uuid_str = str(row[0]).lower()
            if uuid_str not in canonical_data:
                canonical_data[uuid_str] = {
                    "type": "PROJECT",
                    "name": row[1],
                    "source": "DB:projects"
                }

        # 3. Check for Formations
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'formations'")
        if cur.fetchone():
            print("Fetching Formations...")
            cur.execute("SELECT id, name FROM formations")
            formations = cur.fetchall()
            for row in formations:
                uuid_str = str(row[0]).lower()
                canonical_data[uuid_str] = {
                    "type": "FORMATION",
                    "name": row[1],
                    "source": "DB:formations"
                }

        print(f"Total Canonical UUIDs fetched: {len(canonical_data)}")
        return canonical_data
        
    except Exception as e:
        print(f"Error connecting/querying DB: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def run_fetch_db():
    data = fetch_canonical_uuids()
    if data:
        output_dir = os.path.join("artifacts", "omni")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "canonical_uuids.json")
        
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {output_path}")
