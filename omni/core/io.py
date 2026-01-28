import json
from pathlib import Path
from .model import ScanResult

def save_scan(result: ScanResult, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

def load_scan(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)
