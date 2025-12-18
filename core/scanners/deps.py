from pathlib import Path

def scan(target: Path) -> dict:
    """Checks for dependency files."""
    found = []
    
    candidates = ["package.json", "requirements.txt", "pyproject.toml", "Gemfile", "go.mod", "Cargo.toml"]
    for c in candidates:
        if (target / c).exists():
            found.append(c)
            
    return {"found": found}
