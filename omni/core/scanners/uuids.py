import os
import re
from pathlib import Path

# Standard UUID v4 pattern (and others)
UUID_PATTERN = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)

# Exclude list 
# (Merged global exclusions + specific scanner noise)
EXCLUDES = {
    # System / Infra
    "node_modules", ".git", ".venv", "venv", "dist", "build", 
    "__pycache__", ".next", ".firebase", "coverage", "htmlcov",
    "var", "data", "input", "output",
    # Specific artifacts to ignore for identity
    "artifacts", "logs", "backups", "snapshots",
    "INBOX", "archive", "older_versions"
}

IGNORABLE_FILES = (
    ".bak", ".tmp", ".log", ".csv", ".lock",
    "chat-export-", "2024-", "2025-" # Timestamped files
)

def is_toxic_uuid(u: str) -> bool:
    """Returns True if UUID is a placeholder or test-value."""
    u = u.lower()
    if u.startswith("00000000"): return True
    if u.startswith("11111111"): return True
    if u.startswith("22222222"): return True
    # The RFC example UUID
    if u == "550e8400-e29b-41d4-a716-446655440000": return True
    # Sequential test pattern
    if "1234-1234" in u: return True
    return False

def scan(target: Path) -> dict:
    """
    Scans for UUIDs in files.
    """
    found_uuids = {} # uuid -> {total: int, locs: set, per_file: dict}
    total_files_scanned = 0
    
    try:
        for root, dirs, files in os.walk(target):
            # Prune directories in place
            dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('.')]
            
            for file in files:
                # 1. Check file blacklist
                if any(x in file for x in IGNORABLE_FILES):
                    continue

                # 2. Extension whitelist
                if not file.endswith(('.md', '.py', '.json', '.yaml', '.yml', '.txt', '.js', '.ts', '.env', '.html', '.css', '.toml')):
                    continue
                
                path = Path(root) / file
                path_str = str(path)
                
                try:
                    total_files_scanned += 1
                    if total_files_scanned % 1000 == 0:
                        print(f"      [PROG] Scanned {total_files_scanned} files...", end='\r')
                        
                    # Skip massive files
                    if path.stat().st_size > 1024 * 1024: continue # 1MB limit
                    
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    matches = UUID_PATTERN.findall(content)
                    
                    if not matches:
                        continue

                    if not matches:
                        continue

                    # Local count for this file
                    local_counts = {}
                    for m in matches:
                        u = m.lower()
                        if is_toxic_uuid(u): continue
                        local_counts[u] = local_counts.get(u, 0) + 1

                    # Aggregate
                    for u, count in local_counts.items():
                        if u not in found_uuids:
                            found_uuids[u] = {
                                "total": 0,
                                "locations": set(),
                                "counts_by_location": {}
                            }
                        
                        found_uuids[u]["total"] += count
                        found_uuids[u]["locations"].add(path_str)
                        found_uuids[u]["counts_by_location"][path_str] = count

                except Exception:
                    continue
    except Exception as e:
        return {"error": str(e)}

    # Format for JSON output
    items = []
    for u, data in found_uuids.items():
        items.append({
            "uuid": u,
            "locations": list(data["locations"]),
            "counts_by_location": data["counts_by_location"],
            "count": data["total"]
        })
    
    # Sort by count desc
    items.sort(key=lambda x: x["count"], reverse=True)

    return {
        "count": len(items),
        "items": items
    }
