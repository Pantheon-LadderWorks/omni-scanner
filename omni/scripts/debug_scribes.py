import yaml
from pathlib import Path

path = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.remediated.md")
content = path.read_text(encoding="utf-8")
data = yaml.safe_load(content.split("---")[1])

print("--- SCRIBES VARIANTS ---")
for e in data["entities"]:
    cid = e.get("canonical_id", "")
    if "scribes" in cid.lower() and "anvil" in cid.lower():
        print(f"'{cid}' (Len: {len(cid)})")
