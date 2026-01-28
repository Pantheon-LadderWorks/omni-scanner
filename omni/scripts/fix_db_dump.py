import json
from pathlib import Path

dump_path = Path(r"C:\Users\kryst\Infrastructure\tools\artifacts\omni\canonical_uuids.json")
data = json.load(dump_path.open(encoding="utf-8"))

UUID_TO_REMOVE = "fe30b79e-3243-4275-80f7-a564e62328b5"
if UUID_TO_REMOVE in data:
    del data[UUID_TO_REMOVE]
    print(f"✅ Removed duplicate Quantum UUID: {UUID_TO_REMOVE}")
    
    # Save back
    dump_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
else:
    print("ℹ️ UUID to remove not found.")
