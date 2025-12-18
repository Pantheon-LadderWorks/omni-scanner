"""
Canonical UUID Fetcher (Postgres)
Migrated from tools/fetch_canonical_uuids.py
"""
import os
import json
import psycopg2
from typing import Dict, List

# Connection settings
DB_CONFIG = {
    "dbname": os.getenv("CMS_DB_NAME", "cms_db"),
    "user": os.getenv("CMS_DB_USER", "postgres"),
    "password": os.getenv("CMS_DB_PASSWORD", "password"),
    "host": os.getenv("CMS_DB_HOST", "localhost"),
    "port": os.getenv("CMS_DB_PORT", "5433")
}

def fetch_canonical_uuids() -> Dict[str, Dict]:
    print("Connecting to CMS Database...")
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
