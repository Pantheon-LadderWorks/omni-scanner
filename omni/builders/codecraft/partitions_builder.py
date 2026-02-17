"""
build_partitions_lock.py
Build a partition lock for NON-school lexicon content (everything except 02_ARCANE_SCHOOLS).
Canon architecture:
  - canon.lock.yaml          → Pure Arcane Schools (20 schools, Rosetta Archaeologist)
  - canon.partitions.lock.yaml → Everything else (foundations, syntax, operators, params, examples, migrations)

Usage:
    python tools/build_partitions_lock.py

Requirements:
    pip install pyyaml

Output:
    canon.partitions.lock.yaml (in lexicon root)
"""
import sys
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(2)

# ═══════════════════════════════════════════════════════════════════════════
# PARTITION MAPPING - Lexicon folders → Partition names
# ═══════════════════════════════════════════════════════════════════════════

PARTITION_MAP = {
    "01_FOUNDATIONS":      "foundations",
    "03_SYNTAX_VARIANTS":  "syntax_variants",
    "04_PARAMETERS":       "parameters",
    "05_OPERATORS":        "operators",
    "06_EXAMPLES":         "examples",
    "08_MIGRATION":        "migrations",
}

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n?', re.DOTALL)

def load_front_matter(path: Path) -> Dict[str, Any]:
    """Extract YAML front-matter from markdown file."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = FRONT_MATTER_RE.match(text)
        if not m:
            return {}
        return yaml.safe_load(m.group(1)) or {}
    except Exception as e:
        print(f"WARNING: Failed to parse front-matter in {path}: {e}")
        return {}

def stem_to_title(stem: str) -> str:
    """Convert filename stem to Title Case."""
    s = stem.replace("_", " ").replace("-", " ")
    return s.title()

# ═══════════════════════════════════════════════════════════════════════════
# ENTRY BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

def infer_id(partition: str, meta: Dict[str, Any], file_path: Path) -> str:
    """Generate unique ID for entry."""
    # Prefer explicit ID from front-matter
    if "id" in meta:
        return str(meta["id"])
    
    # Fall back to partition.filename pattern
    name = str(meta.get("name") or meta.get("title") or file_path.stem)
    name_slug = re.sub(r'[^a-z0-9]+', "_", name.lower()).strip("_")
    return f"{partition}.{name_slug}"

def infer_kind(partition: str, meta: Dict[str, Any]) -> str:
    """Infer document kind from partition and front-matter."""
    # Explicit kind in front-matter takes precedence
    if "kind" in meta:
        return str(meta["kind"])
    
    # Partition-specific defaults
    kind_map = {
        "foundations": "foundation",
        "syntax_variants": "syntax_variant",
        "parameters": "parameter",
        "operators": "operator",
        "examples": "example",
        "migrations": "migration",
    }
    return kind_map.get(partition, "artifact")

def build_entry(partition: str, lexicon_root: Path, file_path: Path) -> Dict[str, Any]:
    """Build a single partition entry from a markdown file."""
    meta = load_front_matter(file_path)
    
    # Core fields
    kind = infer_kind(partition, meta)
    id_ = infer_id(partition, meta, file_path)
    title = str(meta.get("title") or meta.get("name") or stem_to_title(file_path.stem))
    
    # Version & schema
    version = str(meta.get("schema_version") or meta.get("version") or "1.0")
    
    # Status (if present)
    status = meta.get("status", "active")
    
    # Safety tier (if present)
    safety_tier = meta.get("safety_tier")
    safety = {"tier": safety_tier} if safety_tier is not None else {}
    
    # Relative path from lexicon root
    try:
        rel_path = file_path.relative_to(lexicon_root)
    except ValueError:
        rel_path = file_path
    
    entry = {
        "id": id_,
        "title": title,
        "kind": kind,
        "version": version,
        "status": status,
        "provenance": {
            "path": str(rel_path.as_posix()),
            "absolute_path": str(file_path.as_posix()),
        },
        "hash": sha256_file(file_path),
    }
    
    # Only add safety if present
    if safety:
        entry["safety"] = safety
    
    return entry

# ═══════════════════════════════════════════════════════════════════════════
# MAIN BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def build_partitions_lock(lexicon_root: Path, output_path: Path):
    """Build canon.partitions.lock.yaml from lexicon structure."""
    
    if not lexicon_root.exists():
        print(f"ERROR: Lexicon root not found: {lexicon_root}")
        sys.exit(1)
    
    # Initialize partitions
    partitions = {
        "foundations": [],
        "syntax_variants": [],
        "parameters": [],
        "operators": [],
        "examples": [],
        "migrations": [],
    }
    
    # Scan each partition folder
    for folder_name, partition_name in PARTITION_MAP.items():
        folder_path = lexicon_root / folder_name
        
        if not folder_path.exists():
            print(f"WARNING: Partition folder not found: {folder_path}")
            continue
        
        print(f"Scanning {folder_name}...")
        
        # Find all markdown files (excluding README.md)
        for md_file in folder_path.rglob("*.md"):
            if md_file.name.upper() == "README.MD":
                continue  # Skip navigation files
            
            try:
                entry = build_entry(partition_name, lexicon_root, md_file)
                partitions[partition_name].append(entry)
                print(f"  ✓ {entry['id']}")
            except Exception as e:
                print(f"  ✗ ERROR processing {md_file}: {e}")
    
    # Build lock document
    lock = {
        "schema": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Partition lock for non-school lexicon content (foundations, syntax, operators, parameters, examples, migrations)",
        "architecture": {
            "canon.lock.yaml": "Pure Arcane Schools (20 schools, Rosetta Archaeologist)",
            "canon.partitions.lock.yaml": "Everything else (this file)",
        },
        "partitions": partitions,
    }
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(lock, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
    
    # Summary
    counts = {name: len(entries) for name, entries in partitions.items()}
    total = sum(counts.values())
    
    print("\n" + "="*80)
    print("✅ PARTITION LOCK GENERATED")
    print("="*80)
    print(f"Output: {output_path}")
    print(f"\nPartition Counts:")
    for name, count in counts.items():
        print(f"  - {name:20s}: {count:3d} entries")
    print(f"\n  TOTAL: {total} entries")
    print("="*80)

# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Determine paths relative to script location
    script_dir = Path(__file__).parent
    lexicon_root = (script_dir / "../lexicon").resolve()
    output_path = lexicon_root / "canon.partitions.lock.yaml"
    
    print("CodeCraft Partition Lock Builder")
    print("="*80)
    print(f"Lexicon Root: {lexicon_root}")
    print(f"Output File:  {output_path}")
    print("="*80 + "\n")
    
    build_partitions_lock(lexicon_root, output_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
