"""
UUID Provenance Core Logic
Migrated from tools/audit_provenance.py
"""
import os
import re
import json
import sys
from pathlib import Path
from collections import defaultdict
from omni.core import registry_v2

# Configuration
# Hardcoding roots strictly as requested
WORKSPACE_ROOTS = [
    r"C:\Users\kryst\Infrastructure",
    r"C:\Users\kryst\Deployment",
    r"C:\Users\kryst\Workspace"
]

UUID_PATTERN = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.IGNORECASE)

KNOWN_TEST_UUIDS = {
    "00000000-0000-0000-0000-000000000000",
    "12345678-1234-1234-1234-1234567890ab", 
    "11111111-1111-1111-1111-111111111111",
    "550e8400-e29b-41d4-a716-446655440000", # Example UUID
    "123e4567-e89b-12d3-a456-426614174000"  # Another common example
}

# Directories to ignore
IGNORE_DIRS = {
    'node_modules', '.git', 'dist', 'build', '__pycache__', 
    '.vscode', '.idea', 'coverage', 'tmp', 'temp'
}

# File extensions to ignore
IGNORE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp',
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
    '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar',
    '.db', '.sqlite', '.sqlite3',
    '.wem', '.bnk', '.mp3', '.wav', '.ogg',
    '.ttc', '.ttf', '.woff', '.woff2', '.eot'
}

def scan_uuids_in_file(path):
    """Returns a set of unique UUIDs found in the file."""
    found = set()
    try:
        if path.stat().st_size > 1024 * 1024 * 5: # Skip > 5MB
            return found
            
        text = path.read_text(encoding='utf-8', errors='ignore')
        matches = UUID_PATTERN.findall(text)
        found.update(m.lower() for m in matches)
    except Exception:
        pass
    return found

def run_provenance_audit():
    """Main entry point for provenance audit."""
    print("[*] UUID PROVENANCE INDEX (UPI) GENERATOR [*]")

    # 1. Load Authorities (Registry V2)
    print("\n[1/4] Loading Authorities (Registry V2)...")
    
    canonical_uuids = {} # uuid -> {name, source, type, canonical_id}

    # A. From Registry V2 (Master MD)
    reg_v2_data = registry_v2.load_v2_registry()
    
    if "error" in reg_v2_data:
        print(f"      [ERR] Failed to load Registry V2: {reg_v2_data['error']}")
    else:
        canonical_uuids = reg_v2_data
        print(f"      Loaded {len(canonical_uuids)} Canonical IDs/Facets from Registry V2.")

    # B. From DB Dump (canonical_uuids.json) - Optional Merge/Verify
    db_dump_path = Path("artifacts/omni/canonical_uuids.json") 
    if db_dump_path.exists():
        with open(db_dump_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)
            merged_count = 0
            for u, data in db_data.items():
                if u not in canonical_uuids:
                    # DB has it, Registry doesn't -> Candidate for Registry spec
                    canonical_uuids[u.lower()] = {
                        "type": "DB_ONLY",
                        "kind": data.get('type', 'unknown').lower(),
                        "name": data.get('name'),
                        "source": "DB:dump"
                    }
                    merged_count += 1
            print(f"      Merged {merged_count} additional UUIDs from DB dump.")

    # 2. Scanning Filesystem
    print("\n[2/4] Scanning Filesystem...")
    
    # uuid -> list of {path, context}
    occurrences = defaultdict(list)
    
    total_files = 0
    scanned_files = 0
    
    for root_str in WORKSPACE_ROOTS:
        root_path = Path(root_str)
        if not root_path.exists():
            print(f"      [SKIP] Root not found: {root_path}")
            continue
            
        print(f"      Scanning {root_path}...")
        
        for p in root_path.rglob("*"):
            # Basic ignore
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            
            # STRICT IGNORE: artifacts/omni (Self-Scanning Prevention)
            # This prevents the scanner from reading its own output and creating 14k orphans
            if "artifacts" in p.parts and "omni" in p.parts:
                continue
            
            # STRICT IGNORE: omni/archive
            if "omni" in p.parts and "archive" in p.parts:
                continue

            if p.suffix.lower() in IGNORE_EXTS:
                continue
            if not p.is_file():
                continue
                
            total_files += 1
            # Progress marker
            if total_files % 1000 == 0:
                print(f"      ...{total_files} files...", end='\r')
                
            uuids = scan_uuids_in_file(p)
            if uuids:
                scanned_files += 1
                rel_path = str(p) # Absolute for clarity in reporting
                for u in uuids:
                    occurrences[u].append(rel_path)

    print(f"      Scanned {total_files} files. Found UUIDs in {scanned_files} files.")
    print(f"      Unique UUIDs found: {len(occurrences)}")

    # 3. Categorization & Analysis
    print("\n[3/4] Categorizing...")
    
    provenance_index = {}
    categorized_counts = defaultdict(int)

    # Categories
    CAT_CANONICAL = "CANONICAL"
    CAT_ORPHAN = "ORPHAN"
    CAT_EXTERNAL = "EXTERNAL_LIB"
    CAT_MEMORY = "MEMORY/CACHE"
    CAT_TEST = "TEST/JUNK"
    CAT_UNKNOWN = "UNKNOWN"

    for u, paths in occurrences.items():
        entry = {
            "uuid": u,
            "occurrences": len(paths),
            "paths": paths[:10], # Keep a few more examples
            "category": CAT_UNKNOWN,
            "metadata": {}
        }
        
        # 1. Check Canonical (Highest Authority)
        if u in canonical_uuids:
            auth = canonical_uuids[u]
            entry["category"] = CAT_CANONICAL
            entry["metadata"] = auth
            
        # 2. Check Known Test UUIDs
        elif u in KNOWN_TEST_UUIDS or u.startswith("0000") or u.endswith("000000000000"):
            entry["category"] = CAT_TEST
            
        else:
            # 3. Path-Based Categorization for Non-Canonicals
            # Heuristic: If ALL paths are in "External" dirs, it's an External Lib UUID.
            # If ALL paths are in "Memory" dirs, it's a Memory UUID.
            # If it appears in WORKSPACE but isn't Canonical, it's an Orphan.
            
            is_external = False
            is_memory = False
            is_workspace = False
            
            for p in paths:
                pl = p.lower()
                if "external-frameworks" in pl or "deployment\\external" in pl or "deployment/external" in pl:
                    is_external = True
                elif ".serena" in pl or "janus' memories" in pl or "antigravity" in pl or "memories" in pl:
                    is_memory = True
                else:
                    is_workspace = True
            
            if is_workspace:
                entry["category"] = CAT_ORPHAN
            elif is_external:
                entry["category"] = CAT_EXTERNAL
            elif is_memory:
                entry["category"] = CAT_MEMORY
            else:
                entry["category"] = CAT_ORPHAN # Default fall-through
        
        # Override: If it's Canonical but found in External, it's still Canonical (we own it, but vendor uses it?)
        # Current logic preserves Canonical priority.

        provenance_index[u] = entry
        categorized_counts[entry["category"]] += 1

    # 4. Reporting
    print("\n[4/4] Generating Report...")
    
    output_dir = Path("artifacts/omni")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_out = output_dir / "uuid_provenance.json"
    backup_out = output_dir / "uuid_provenance.json.BACKUP"

    # PHOENIX PROTOCOL: Rotate Backup
    if json_out.exists():
        try:
            # Simple overwrite copy/move
            # We want to keep the old one as backup, so we read it or move it.
            # verify permissions?
            import shutil
            shutil.copy2(json_out, backup_out)
            print(f"      [BACKUP] Rotated previous index to {backup_out.name}")
        except Exception as e:
            print(f"      [WARN] Backup rotation failed: {e}")
    
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(provenance_index, f, indent=2)
        
    print(f"      Index saved to {json_out}")
    
    # Generate MD Report
    md_out = output_dir / "UUID_AUDIT_REPORT.md"
    generate_md_report(md_out, provenance_index, categorized_counts, canonical_uuids)
    print(f"      Report saved to {md_out}")

def generate_md_report(path, index, counts, canonicals):
    md = "# UUID Provenance Report\n\n"
    md += "## Summary\n"
    md += "| Category | Count |\n|---|---|\n"
    for cat, count in counts.items():
        md += f"| {cat} | {count} |\n"
        
    # Ghost Detection (Canonical but NOT found in files)
    ghosts = []
    for u, data in canonicals.items():
        if u not in index:
            ghosts.append(data)
            
    md += f"| **GHOSTS** | {len(ghosts)} |\n"
    md += "\n*Ghosts are Canonical UUIDs that were NOT found in the filesystem scan.*\n"
    
    md += "\n## 1. Ghosts (Missing Wiring)\n"
    if ghosts:
        md += "| Name | Type | Canonical ID | Source |\n|---|---|---|---|\n"
        for g in ghosts:
            md += f"| {g.get('name')} | {g.get('type')} | {g.get('canonical_id','-')} | {g.get('source')} |\n"
    else:
        md += "✅ No Ghosts found. All canonical entities are wired.\n"

    md += "\n## 2. Orphans (Top 20 by Occurrence)\n"
    orphans = [v for k,v in index.items() if v['category'] == 'ORPHAN']
    orphans.sort(key=lambda x: x['occurrences'], reverse=True)
    
    md += "| UUID | Occurrences | Context (First Match) |\n|---|---|---|\n"
    for o in orphans[:20]:
         path_sample = o['paths'][0] if o['paths'] else "-"
         # shorten path
         path_sample = path_sample[-50:] if len(path_sample) > 50 else path_sample
         md += f"| `{o['uuid']}` | {o['occurrences']} | `...{path_sample}` |\n"
         
    path.write_text(md, encoding='utf-8')
