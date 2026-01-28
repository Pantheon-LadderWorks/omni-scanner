import json
from pathlib import Path
from collections import defaultdict

def analyze():
    p = Path("artifacts/omni/uuid_provenance.json")
    if not p.exists():
        print("File not found.")
        return

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    counts = defaultdict(int)
    
    # Sub-categories for Memory/Unknown
    mem_janus = 0
    mem_antigravity = 0
    mem_serena = 0
    mem_other = 0
    
    orphans = 0
    external = 0
    canonical = 0
    test = 0
    
    for u, entry in data.items():
        cat = entry.get("category", "UNKNOWN")
        paths = entry.get("paths", [])
        
        if cat == "CANONICAL":
            canonical += 1
        elif cat == "EXTERNAL_LIB":
            external += 1
        elif cat == "TEST/JUNK":
            test += 1
        elif cat == "MEMORY/CACHE":
            # Breakdown
            is_j = any("janus' memories" in p.lower() for p in paths)
            is_a = any("antigravity" in p.lower() for p in paths)
            is_s = any(".serena" in p.lower() for p in paths)
            
            if is_j: mem_janus += 1
            if is_a: mem_antigravity += 1
            if is_s: mem_serena += 1
            if not (is_j or is_a or is_s): mem_other += 1
            
        elif cat == "ORPHAN" or cat == "UNKNOWN":
            orphans += 1
        
        counts[cat] += 1

    print("--- UUID ANALYSIS ---")
    print(f"Total UUIDs: {len(data)}")
    print(f"Canonical: {canonical}")
    print(f"External Libs: {external}")
    print(f"Test/Junk: {test}")
    print(f"Orphans/Unknown: {orphans}")
    print("--- MEMORY BREAKDOWN ---")
    print(f"Janus Memories: {mem_janus}")
    print(f"Antigravity Sessions: {mem_antigravity}")
    print(f"Other Memory: {mem_other}")

    # --- CANONICAL SOURCE ANALYSIS (Registry vs DB) ---
    print("\n--- REGISTRY VS DATABASE AUDIT ---")
    reg_count = 0
    db_count = 0
    merged_count = 0
    
    db_only = []
    reg_only = []
    
    for u, entry in data.items():
        if entry.get("category") == "CANONICAL":
            src = entry.get("metadata", {}).get("source", "Unknown")
            name = entry.get("metadata", {}).get("name", "Unknown")
            
            if "REGISTRY_V2" in src:
                reg_count += 1
                # If we had a way to know if it was ALSo in DB, we'd count merged. 
                # But provenance.py merges them. If DB was loaded second, it might overwrite?
                # Actually provenance.py loads Reg first, then DB. 
                # If DB entry exists, it acts as "additional".
                # Let's list the ones labeled 'DB:' - these are NOT in the Registry V2 (because if they were, Reg V2 would have taken precedence or been listed).
                # Wait, check provenance.py merge logic.
                pass
            elif "DB" in src:
                db_count += 1
                db_only.append((name, u))
    
    print(f"Registry V2 Entities: {reg_count} (Modern)")
    print(f"Legacy DB Entities:   {db_count} (Potential Ghosts/Old)")
    
    if db_only:
        print("\n[!] LEGACY DB ENTITIES (Not in MASTER.md):")
        for name, u in db_only:
            print(f"  - {name:<30} {u}")

    # --- TRINITY CHECK PROTOOTYPE ---
    print("\n--- TRINITY COMPLIANCE (Top 10 Ghosts/Partial) ---")
    print(f"{'Name':<30} | {'Reg':<5} | {'Code':<5} | {'Conf':<5} | {'UUID'}")
    print("-" * 80)
    
    # Heuristics for File Types
    CODE_EXTS = {'.py', '.js', '.ts', '.rs', '.go', '.cpp', '.c', '.java'}
    CONFIG_FILES = {'pyproject.toml', 'package.json', 'project.yml', 'cargo.toml', 'requirements.txt'}

    count = 0
    for u, entry in data.items():
        if entry.get("category") != "CANONICAL":
            continue
            
        meta = entry.get("metadata", {})
        name = meta.get("name", "Unknown")
        paths = entry.get("paths", [])
        
        has_reg = True # By definition if CAT=CANONICAL
        has_code = False
        has_config = False
        
        for p in paths:
            pl = p.lower()
            fname = Path(p).name.lower()
            ext = Path(p).suffix.lower()
            
            if ext in CODE_EXTS:
                has_code = True
            if fname in CONFIG_FILES or fname.endswith(".yml") or fname.endswith(".json"):
                has_config = True
        
        # We want to show items that represent "Real" entities but might be missing something
        # or fully compliant ones.
        # Let's show ones that are MISSING parts first.
        
        status_code = "YES" if has_code else "NO"
        status_conf = "YES" if has_config else "NO"
        
        # Only print if valid entity name (skip simple IDs if needed)
        count += 1
        if count <= 20: 
             print(f"{name[:30]:<30} | YES   | {status_code:<5} | {status_conf:<5} | {u}")

if __name__ == "__main__":
    analyze()
