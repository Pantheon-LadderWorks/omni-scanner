from pathlib import Path

def scan(target: Path) -> dict:
    """Checks for core documentation."""
    required = ["README.md", "ARCHITECTURE.md", "CONTRACT.md"]
    found = []
    missing = []
    
    for req in required:
        if (target / req).exists():
            found.append(req)
        else:
            missing.append(req)
            
    # Avoid div by zero
    score = len(found)/len(required) if required else 0.0
            
    return {"found": found, "missing": missing, "score": score}
