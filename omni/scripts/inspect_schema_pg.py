"""
inspect_schema_pg.py
Description: X-rays the Postgres database to reveal table structure and column names.
             Adapted from Ace's SQLite script for the Live Postgres Environment.
"""

import psycopg2
import os
from dotenv import load_dotenv

import sys
# Force UTF-8 Output for Windows Console/File Redirection
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import sys
import os
import getpass
import psycopg2
from dotenv import load_dotenv

# Load .env variables (if available)
load_dotenv()

# Force UTF-8 Output for Windows Console/File Redirection
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
    # Interactive fallback (no echo)
    return getpass.getpass("Postgres password (CMS_DB_PASSWORD): ")

def get_db_connection():
    # Sanity check: Ensure no inline password leaked into the static config
    if "password" in DB_CONFIG:
        raise RuntimeError("🚨 SECURITY ALERT: Inline DB password detected in source. Use CMS_DB_PASSWORD env var.")
    
    cfg = dict(DB_CONFIG)
    cfg["password"] = get_db_password()
    return psycopg2.connect(**cfg)

def inspect_db():
    # Mask password for display
    safe_config = dict(DB_CONFIG)
    print(f"🔍 Inspecting Postgres Schema for: {safe_config['dbname']} @ {safe_config['host']}:{safe_config['port']}")
    print("-" * 60)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Get all table names (public schema)
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()

        if not tables:
            print("⚠️  No tables found in the database.")
        
        for table in tables:
            table_name = table[0]
            print(f"\n📂 TABLE: [{table_name}]")
            
            # 2. Get column details
            # columns: (column_name, data_type, is_nullable)
            cursor.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table_name}';")
            columns = cursor.fetchall()
            
            # Get PKs
            cursor.execute(f"""
                SELECT a.attname
                FROM   pg_index i
                JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                     AND a.attnum = ANY(i.indkey)
                WHERE  i.indrelid = '{table_name}'::regclass
                AND    i.indisprimary;
            """)
            pks = [row[0] for row in cursor.fetchall()]

            print(f"   {'Column Name':<25} | {'Type':<15} | {'PK'}")
            print(f"   {'-'*25} | {'-'*15} | {'--'}")
            
            for col in columns:
                c_name = col[0]
                c_type = col[1]
                c_pk = "🔑" if c_name in pks else ""
                print(f"   {c_name:<25} | {c_type:<15} | {c_pk}")
                
            # 3. Peek at the first row
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                first_row = cursor.fetchone()
                if first_row:
                    # Convert to string to avoid messy output
                    print(f"   👀 Sample Row: {str(first_row)[:100]}...") 
            except Exception as e:
                print(f"   (Could not fetch sample: {e})")

        conn.close()
        print("\n" + "-" * 60)
        print("✅ Inspection Complete.")

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    inspect_db()
