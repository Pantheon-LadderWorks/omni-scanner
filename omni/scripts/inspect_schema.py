"""
inspect_schema.py
Description: X-rays the SQLite database to reveal table structure and column names.
             Prerequisite for the Zero-Guess Hydration Protocol.
Author: Kode_Animator & Ace
"""

import sqlite3
import os

# Define path explicitly based on your context
DB_PATH = r"C:\Users\kryst\Infrastructure\context\knowledge_base.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        return

    print(f"🔍 Inspecting Schema for: {DB_PATH}")
    print("-" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("⚠️  No tables found in the database.")
        
        for table in tables:
            table_name = table[0]
            print(f"\n📂 TABLE: [{table_name}]")
            
            # 2. Get column details for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Format: (cid, name, type, notnull, dflt_value, pk)
            print(f"   {'Column Name':<20} | {'Type':<10} | {'PK'}")
            print(f"   {'-'*20} | {'-'*10} | {'--'}")
            
            for col in columns:
                c_name = col[1]
                c_type = col[2]
                c_pk = "🔑" if col[5] else ""
                print(f"   {c_name:<20} | {c_type:<10} | {c_pk}")
                
            # 3. Peek at the first row to see what data looks like
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                first_row = cursor.fetchone()
                if first_row:
                    print(f"   👀 Sample Row: {first_row}")
            except Exception as e:
                print(f"   (Could not fetch sample: {e})")

        conn.close()
        print("\n" + "-" * 60)
        print("✅ Inspection Complete.")

    except sqlite3.Error as e:
        print(f"❌ SQLite Error: {e}")

if __name__ == "__main__":
    inspect_db()
