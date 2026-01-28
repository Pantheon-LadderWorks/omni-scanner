"""
build_executors_lock.py
Build the Runtime Lock (canon.executors.lock.yaml) from executors.canonical.yaml.

This is the THIRD LOCK in the Triple-Lock Sovereignty system:
  - canon.lock.yaml             → Language Lock (WHAT you can say - 20 Arcane Schools)
  - canon.partitions.lock.yaml  → Knowledge Lock (HOW to learn - foundations, syntax, etc.)
  - canon.executors.lock.yaml   → Runtime Lock (WHO can execute - VM identity & authority)

Usage:
    python tools/build_executors_lock.py

Requirements:
    pip install pyyaml

Output:
    canon.executors.lock.yaml (in lexicon root)
"""
import sys
import os
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
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text: str) -> str:
    """Compute SHA-256 hash of text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ═══════════════════════════════════════════════════════════════════════════
# LOCK BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def validate_executor(executor: Dict[str, Any], idx: int) -> bool:
    """Validate executor structure."""
    required_fields = ["id", "tier", "description", "bridge", "jurisdiction", "capabilities", "guardrails"]
    
    for field in required_fields:
        if field not in executor:
            print(f"  ✗ ERROR: Executor #{idx} missing required field: {field}")
            return False
    
    # Validate tier format (T1, T2, T3)
    tier = executor["tier"]
    if not isinstance(tier, str) or tier not in ["T1", "T2", "T3"]:
        print(f"  ✗ ERROR: Executor '{executor['id']}' has invalid tier: {tier} (must be T1, T2, or T3)")
        return False
    
    # Validate jurisdiction is a list
    if not isinstance(executor["jurisdiction"], list):
        print(f"  ✗ ERROR: Executor '{executor['id']}' jurisdiction must be a list")
        return False
    
    # Validate capabilities is a list
    if not isinstance(executor["capabilities"], list):
        print(f"  ✗ ERROR: Executor '{executor['id']}' capabilities must be a list")
        return False
    
    # Validate guardrails is a list
    if not isinstance(executor["guardrails"], list):
        print(f"  ✗ ERROR: Executor '{executor['id']}' guardrails must be a list")
        return False
    
    return True

def build_executors_lock(source_path: Path, output_path: Path):
    """Build canon.executors.lock.yaml from executors.canonical.yaml."""
    
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        sys.exit(1)
    
    print(f"Loading source: {source_path}")
    
    # Load source YAML
    with open(source_path, "r", encoding="utf-8") as f:
        source_data = yaml.safe_load(f)
    
    if not source_data:
        print("ERROR: Source file is empty or invalid YAML")
        sys.exit(1)
    
    if "executors" not in source_data:
        print("ERROR: Source file missing 'executors' key")
        sys.exit(1)
    
    executors = source_data["executors"]
    
    if not isinstance(executors, list):
        print("ERROR: 'executors' must be a list")
        sys.exit(1)
    
    print(f"Found {len(executors)} executors")
    print()
    
    # Validate all executors
    validated_executors = []
    for idx, executor in enumerate(executors, 1):
        if validate_executor(executor, idx):
            validated_executors.append(executor)
            print(f"  ✓ {executor['id']:15s} (Tier {executor['tier']}, {len(executor['jurisdiction'])} jurisdictions)")
        else:
            print(f"  ✗ Validation failed for executor #{idx}")
            sys.exit(1)
    
    # Compute source hash
    source_hash = sha256_file(source_path)
    
    # Build lock document
    lock = {
        "schema": "1.0",
        "lock_type": "runtime",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Runtime Lock - Defines WHO is allowed to execute CodeCraft rituals (VM identity, tier, jurisdiction, authority, guardrails)",
        "triple_lock_architecture": {
            "lock_1": "canon.lock.yaml - Language Lock (WHAT you can say - 20 Arcane Schools)",
            "lock_2": "canon.partitions.lock.yaml - Knowledge Lock (HOW to learn - foundations, syntax, operators, etc.)",
            "lock_3": "canon.executors.lock.yaml - Runtime Lock (WHO can execute - THIS FILE)",
        },
        "provenance": {
            "source_file": str(source_path.name),
            "source_path": str(source_path.as_posix()),
            "source_hash": source_hash,
            "generator": "build_executors_lock.py",
            "version": source_data.get("version", "1.0.0"),
        },
        "executors": validated_executors,
        "statistics": {
            "total_executors": len(validated_executors),
            "tier_breakdown": {
                "T1": sum(1 for e in validated_executors if e["tier"] == "T1"),
                "T2": sum(1 for e in validated_executors if e["tier"] == "T2"),
                "T3": sum(1 for e in validated_executors if e["tier"] == "T3"),
            },
        },
    }
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(lock, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
    
    # Summary
    print("\n" + "="*80)
    print("✅ RUNTIME LOCK GENERATED")
    print("="*80)
    print(f"Output: {output_path}")
    print(f"\nExecutor Counts by Tier:")
    print(f"  - Tier 1 (Safe/Sandboxed):        {lock['statistics']['tier_breakdown']['T1']} executors")
    print(f"  - Tier 2 (Controlled Effects):    {lock['statistics']['tier_breakdown']['T2']} executors")
    print(f"  - Tier 3 (QEE Governance):        {lock['statistics']['tier_breakdown']['T3']} executors")
    print(f"\n  TOTAL: {lock['statistics']['total_executors']} executors")
    print(f"\nSource Hash: {source_hash[:16]}...")
    print("="*80)
    print()
    print("🏛️ TRIPLE-LOCK SOVEREIGNTY COMPLETE")
    print("   Lock 1: canon.lock.yaml (Language - 20 Arcane Schools)")
    print("   Lock 2: canon.partitions.lock.yaml (Knowledge - Foundations, Syntax, etc.)")
    print("   Lock 3: canon.executors.lock.yaml (Runtime - VM Identity & Authority)")
    print("="*80)

# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Determine paths relative to script location
    script_dir = Path(__file__).parent
    lexicon_root = (script_dir / "../lexicon").resolve()
    source_path = lexicon_root / "executors.canonical.yaml"
    output_path = lexicon_root / "canon.executors.lock.yaml"
    
    print("CodeCraft Runtime Lock Builder")
    print("="*80)
    print(f"Lexicon Root:  {lexicon_root}")
    print(f"Source File:   {source_path}")
    print(f"Output File:   {output_path}")
    print("="*80 + "\n")
    
    build_executors_lock(source_path, output_path)

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
