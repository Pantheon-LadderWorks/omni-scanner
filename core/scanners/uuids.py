import os
import re
from pathlib import Path

# Standard UUID v4 pattern (and others)
UUID_PATTERN = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)

# Exclude list (extending the global one ideally, but local here for now)
EXCLUDES = {
    "node_modules", ".git", ".venv", "venv", "dist", "build", 
    "__pycache__", ".next", ".firebase", "coverage", "htmlcov"
}

def scan(target: Path) -> dict:
    """
    Scans for UUIDs in files.
    """
    found_uuids = {} # map uuid -> list of locations
    total_files_scanned = 0
    
    try:
        for root, dirs, files in os.walk(target):
            # Prune directories in place
            dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('.')]
            
            for file in files:
                # Text files only roughly
                if not file.endswith(('.md', '.py', '.json', '.yaml', '.yml', '.txt', '.js', '.ts', '.env', '.html', '.css', '.toml')):
                    continue
                
                path = Path(root) / file
                try:
                    total_files_scanned += 1
                    if total_files_scanned % 1000 == 0:
                        print(f"      [PROG] Scanned {total_files_scanned} files...", end='\r')
                        
                    # Skip massive files
                    if path.stat().st_size > 1024 * 1024: continue # 1MB limit
                    
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    matches = UUID_PATTERN.findall(content)
                    
                    for uuid_str in matches:
                        u = uuid_str.lower()
                        if u not in found_uuids:
                            found_uuids[u] = []
                        
                        # Dedup location per file
                        loc = f"{path.name}"
                        if loc not in found_uuids[u]:
                             found_uuids[u].append(str(path))
                except Exception:
                    continue
    except Exception as e:
        return {"error": str(e)}

    # Format for JSON output
    items = []
    for u, locs in found_uuids.items():
        items.append({
            "uuid": u,
            "locations": locs,
            "count": len(locs)
        })

    return {
        "count": len(items),
        "items": items
    }
