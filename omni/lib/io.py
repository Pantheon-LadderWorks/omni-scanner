import json
from pathlib import Path
from uuid import UUID
from omni.core.model import ScanResult

class UUIDEncoder(json.JSONEncoder):
    """JSON encoder that can handle UUID objects."""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

def save_scan(result: ScanResult, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2, cls=UUIDEncoder)

def load_scan(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)
