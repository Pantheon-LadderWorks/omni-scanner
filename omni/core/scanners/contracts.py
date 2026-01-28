from pathlib import Path

def scan(target: Path) -> dict:
    """Checks for contracts like CONTRACT.md or openapi.json."""
    found = []
    
    # Simple check for now
    candidates = ["CONTRACT.md", "openapi.json", "openapi.yaml"]
    for c in candidates:
        if (target / c).exists():
           found.append(c)
           
    return {
        "found": found,
        "count": len(found)
    }
