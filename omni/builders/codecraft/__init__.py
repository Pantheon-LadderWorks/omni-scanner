"""
Canon Lock Builders - Omni Integration
=======================================
The Science Officer's responsibility: Build and maintain The Law.

This module orchestrates all 3 canon lock builders:
1. rosetta_archaeologist → canon.lock.yaml (Language Lock - WHAT)
2. partitions_builder → canon.partitions.lock.yaml (Knowledge Lock - HOW)
3. executors_builder → canon.executors.lock.yaml (Runtime Lock - WHO)

Authority: C-SYS-SPINE-001 (Federation Spine Integration)
Status: Phase 1 - Omni Integration
Date: January 10, 2026
"""
from pathlib import Path
from typing import Optional

# Canon builders will be imported from this package
__all__ = [
    'rebuild_all',
    'rebuild_language',
    'rebuild_partitions',
    'rebuild_executors',
    'verify_all',
    'hash_all',
]

def get_codecraft_root() -> Path:
    """Get CodeCraft language root via Federation Heart path resolution."""
    from omni.config.settings import get_languages_path
    return get_languages_path() / "codecraft"

def get_output_dir() -> Path:
    """
    Get canon lock output directory (codecraft-native/canon/).
    
    Co-located with the VM for fast validation - the VM is the primary consumer.
    When we integrate the builder into the VM workflow, this path is already correct.
    Uses Federation Heart's path resolution for consistency.
    """
    from omni.config.settings import get_languages_path
    # Output directly to VM canon directory
    output = get_languages_path() / "codecraft-native" / "canon"
    output.mkdir(parents=True, exist_ok=True)
    return output

def rebuild_all(
    language: bool = True,
    partitions: bool = True,
    executors: bool = True,
    output_dir: Optional[Path] = None
) -> dict:
    """
    Rebuild all canon locks.
    
    Args:
        language: Rebuild canon.lock.yaml (default True)
        partitions: Rebuild canon.partitions.lock.yaml (default True)
        executors: Rebuild canon.executors.lock.yaml (default True)
        output_dir: Output directory (default: governance/registry/languages)
    
    Returns:
        dict with status of each lock rebuild
    """
    results = {}
    output = output_dir or get_output_dir()
    
    print(f"🏛️  CANON LOCK REBUILD")
    print(f"    Output: {output}")
    print("=" * 70)
    
    if language:
        print("\n📜 Building Language Lock (canon.lock.yaml)...")
        try:
            rebuild_language(output)
            results['language'] = '✅ SUCCESS'
        except Exception as e:
            results['language'] = f'❌ FAILED: {e}'
            print(f"    {results['language']}")
    
    if partitions:
        print("\n📚 Building Knowledge Lock (canon.partitions.lock.yaml)...")
        try:
            rebuild_partitions(output)
            results['partitions'] = '✅ SUCCESS'
        except Exception as e:
            results['partitions'] = f'❌ FAILED: {e}'
            print(f"    {results['partitions']}")
    
    if executors:
        print("\n🔐 Building Runtime Lock (canon.executors.lock.yaml)...")
        try:
            rebuild_executors(output)
            results['executors'] = '✅ SUCCESS'
        except Exception as e:
            results['executors'] = f'❌ FAILED: {e}'
            print(f"    {results['executors']}")
    
    print("\n" + "=" * 70)
    print("🎉 CANON LOCK REBUILD COMPLETE")
    for lock_type, status in results.items():
        print(f"    {lock_type:15s} → {status}")
    
    return results

def rebuild_language(output_dir: Optional[Path] = None):
    """
    Rebuild canon.lock.yaml (Language Lock - 20 Arcane Schools).
    
    This is the PRIMARY law - everything else is drift.
    """
    from .rosetta_archaeologist import build_canon
    
    codecraft_root = get_codecraft_root()
    output = output_dir or get_output_dir()
    
    # Build args namespace (matching rosetta_archaeologist CLI)
    class Args:
        root = str(codecraft_root)
        schools = 'lexicon/schools.canonical.yaml'
        schools_dir = 'lexicon/02_ARCANE_SCHOOLS'
        ebnf = 'lexicon/grammar/lexicon.ebnf'
        grammar_map = 'lexicon/grammar/EBNF_TO_PARSER_MAPPING.md'
        law = 'spec/LAW_AND_LORE_PROTOCOL.md'
        commentomancy = 'lexicon/commentomancy'
        out = str(output / 'canon.lock.yaml')
        render_rosetta = False
        rosetta_path = 'CODECRAFT_ROSETTA_STONE.md'
    
    args = Args()
    
    # Build canon lock
    canon = build_canon(codecraft_root, args)
    
    # Write to output
    import yaml
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        yaml.safe_dump(canon, f, sort_keys=False, allow_unicode=True)
    
    print(f"    ✅ Wrote {args.out}")
    
    # Emit diagnostics if present
    diag = canon.get("diagnostics")
    if diag and diag.get("errors"):
        print("\n    ❌ DRIFT DETECTED:")
        for e in diag["errors"]:
            print(f"       - {e}")
        raise ValueError("Canon lock has drift errors")

def rebuild_partitions(output_dir: Optional[Path] = None):
    """Rebuild canon.partitions.lock.yaml (Knowledge Lock)."""
    from .partitions_builder import build_partitions_lock
    
    codecraft_root = get_codecraft_root()
    output = output_dir or get_output_dir()
    
    lexicon_root = codecraft_root / "lexicon"
    output_path = output / "canon.partitions.lock.yaml"
    
    build_partitions_lock(lexicon_root, output_path)

def rebuild_executors(output_dir: Optional[Path] = None):
    """Rebuild canon.executors.lock.yaml (Runtime Lock)."""
    from .executors_builder import build_executors_lock
    
    codecraft_root = get_codecraft_root()
    output = output_dir or get_output_dir()
    
    lexicon_root = codecraft_root / "lexicon"
    source_path = lexicon_root / "executors.canonical.yaml"
    output_path = output / "canon.executors.lock.yaml"
    
    build_executors_lock(source_path, output_path)

def verify_all():
    """Verify all canon locks for integrity."""
    output = get_output_dir()
    
    print("🔍 CANON LOCK VERIFICATION")
    print("=" * 70)
    
    # Import verify functions from builders
    from .rosetta_archaeologist import cmd_verify as verify_language
    
    # Verify language lock
    class Args:
        canon = str(output / "canon.lock.yaml")
    
    print("\n📜 Verifying Language Lock...")
    try:
        result = verify_language(Args())
        if result == 0:
            print("    ✅ Language lock verified")
        else:
            print("    ❌ Language lock verification failed")
    except Exception as e:
        print(f"    ❌ ERROR: {e}")
    
    # TODO: Add partition and executor verification
    print("\n" + "=" * 70)

def hash_all():
    """Print hashes of all canon locks."""
    output = get_output_dir()
    
    print("🔐 CANON LOCK HASHES")
    print("=" * 70)
    
    from .rosetta_archaeologist import sha256_path
    
    for lock_file in ['canon.lock.yaml', 'canon.partitions.lock.yaml', 'canon.executors.lock.yaml']:
        path = output / lock_file
        if path.exists():
            digest = sha256_path(path)
            print(f"{lock_file:35s} {digest[:16]}...")
        else:
            print(f"{lock_file:35s} NOT FOUND")
    
    print("=" * 70)
