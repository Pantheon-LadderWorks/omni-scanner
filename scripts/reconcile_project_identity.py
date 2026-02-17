#!/usr/bin/env python3
"""
Project Identity Reconciliation Script (Phase A)

The "Hard Lock" - Offline, deterministic, patch-based reconciliation.

This script:
1. Loads all identity sources (GitHub, CMP, Master Registry)
2. Uses omni.core.identity_engine to resolve identities
3. Produces idempotent artifacts:
   - scan.project_identity.json (State Snapshot)
   - project_identity.patch.json (Action Plan)

Policy C: On UUID conflicts, FREEZE - don't overwrite, flag for adjudication.

Usage:
    python reconcile_project_identity.py [--dry-run] [--verbose]
"""

import json
import yaml
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add omni to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omni.core.identity_engine import (
    NAMESPACE_CMP,
    RepoInventoryItem,
    ProjectIdentity,
    IdentityScanResult,
    IdentityScanStats,
    IdentityPatch,
    IdentityPatchAction,
    mint_uuid_v5,
    normalize_github_url,
    extract_project_key_from_url,
)

# Use settings shim for path resolution (Federation Heart integration)
from omni.config.settings import (
    get_repo_inventory_path,
    get_cmp_registry_path,
    get_master_registry_path,
    get_omni_artifacts_path,
    status as heart_status,
)


# =============================================================================
# LOADERS
# =============================================================================

def load_repo_inventory() -> List[Dict]:
    """Load GitHub repos from repo_inventory.json."""
    repo_path = get_repo_inventory_path()
    if not repo_path.exists():
        print(f"[WARN] repo_inventory.json not found at {repo_path}")
        return []
    
    with open(repo_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    return data.get('repos', data.get('items', []))


def load_cmp_registry() -> Dict[str, Dict]:
    """
    Load CMP project registry and build lookup by project_key.
    Returns: {project_key: {local_paths, classification, ...}}
    """
    cmp_path = get_cmp_registry_path()
    if not cmp_path.exists():
        print(f"[WARN] CMP registry not found at {cmp_path}")
        return {}
    
    with open(cmp_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    lookup = {}
    for proj in data.get('projects', []):
        # Extract project key from primary_repo
        primary_repo = proj.get('primary_repo') or ''
        if primary_repo:
            key = extract_project_key_from_url(primary_repo)
            if key:
                lookup[key] = {
                    'display_name': proj.get('display_name'),
                    'local_paths': proj.get('local_paths', []),
                    'classification': proj.get('classification'),
                    'status': proj.get('status'),
                    'tags': proj.get('tags', []),
                }
    
    return lookup


def load_master_registry_uuids() -> Dict[str, str]:
    """
    Extract UUIDs from PROJECT_REGISTRY_MASTER.md frontmatter.
    Returns: {project_key: uuid}
    
    The master registry uses canonical_id, so we need to map
    canonical_id -> project_key for matching.
    """
    master_path = get_master_registry_path()
    if not master_path.exists():
        print(f"[WARN] Master registry not found at {master_path}")
        return {}
    
    uuid_map = {}
    
    with open(master_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.startswith('---'):
        return {}
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}
    
    try:
        data = yaml.safe_load(parts[1])
        entities = data.get('entities', [])
        
        for entity in entities:
            canonical_id = entity.get('canonical_id', '')
            kind = entity.get('kind', '')
            facets = entity.get('facets', {})
            
            # Get UUID from facets.core.id
            core = facets.get('core', {})
            entity_uuid = core.get('id', '')
            
            # Get repo info if available
            repo = facets.get('repo', {})
            primary_repo = repo.get('primary_repo', '')
            
            if entity_uuid:
                # Try to build project_key from primary_repo
                if primary_repo:
                    key = extract_project_key_from_url(primary_repo)
                    if key:
                        uuid_map[key] = entity_uuid
                
                # Also store by canonical_id pattern for fallback matching
                # Convert canonical_id to potential project_key
                slug = canonical_id.lower().replace('_', '-')
                # Store with common owner patterns
                for owner in ['kryssie6985', 'pantheon-ladderworks']:
                    fallback_key = f"github:{owner}/{slug}"
                    if fallback_key not in uuid_map:
                        uuid_map[fallback_key] = entity_uuid
                        
    except yaml.YAMLError as e:
        print(f"[WARN] Failed to parse master registry: {e}")
    
    return uuid_map


# =============================================================================
# MAIN RECONCILIATION
# =============================================================================

def reconcile(verbose: bool = False) -> tuple[IdentityScanResult, IdentityPatch]:
    """
    Main reconciliation logic.
    
    Returns: (scan_result, patch)
    """
    print("[RECON] Phase A: Identity-First Reconciliation")
    print(f"[RECON] Namespace: {NAMESPACE_CMP}")
    print("=" * 60)
    
    # Step 0: Load all sources
    print("\n[STEP 0] Loading sources...")
    
    github_repos = load_repo_inventory()
    print(f"  GitHub repos: {len(github_repos)}")
    
    cmp_data = load_cmp_registry()
    print(f"  CMP projects (with keys): {len(cmp_data)}")
    
    legacy_oracle = load_master_registry_uuids()
    print(f"  Master UUIDs: {len(legacy_oracle)}")
    
    # Step 1: Resolve identities
    print("\n[STEP 1] Resolving identities...")
    
    projects: List[ProjectIdentity] = []
    actions: List[IdentityPatchAction] = []
    seen_keys = set()  # Track duplicates
    
    stats = IdentityScanStats()
    
    for repo_data in github_repos:
        try:
            repo = RepoInventoryItem(**repo_data)
        except Exception as e:
            if verbose:
                print(f"  [SKIP] Failed to parse repo: {e}")
            continue
        
        # Check for duplicates (same project in personal + org)
        if repo.project_key in seen_keys:
            if verbose:
                print(f"  [DUP] Skipping duplicate: {repo.project_key}")
            continue
        seen_keys.add(repo.project_key)
        
        # Resolve identity
        identity = ProjectIdentity.resolve(
            repo,
            existing_db_map={},  # No live DB in Phase A
            legacy_oracle=legacy_oracle,
            cmp_data=cmp_data
        )
        projects.append(identity)
        
        # Update stats
        stats.total += 1
        stats.from_github += 1
        
        if identity.uuid_source == "master_registry":
            stats.has_uuid_from_master += 1
        elif identity.uuid_source == "minted_v5":
            stats.needs_uuid_minted += 1
        
        if identity.cmp_status == "found":
            stats.in_cmp += 1
        else:
            stats.not_in_cmp += 1
        
        if identity.local_paths:
            stats.has_local_path += 1
        
        if identity.identity_status == "conflict":
            stats.conflicts += 1
        
        # Generate patch action
        if identity.identity_status == "conflict":
            actions.append(IdentityPatchAction(
                action_type="CONFLICT_FREEZE",
                project_key=identity.project_key,
                project_uuid=identity.project_uuid,
                severity="critical",
                payload={"conflict": identity.conflict_details}
            ))
        elif identity.cmp_status == "not_found":
            actions.append(IdentityPatchAction(
                action_type="CMP_CREATE",
                project_key=identity.project_key,
                project_uuid=identity.project_uuid,
                severity="info",
                payload={
                    "name": identity.name,
                    "github_url": identity.github_url,
                    "description": identity.description,
                }
            ))
        else:
            actions.append(IdentityPatchAction(
                action_type="NO_OP",
                project_key=identity.project_key,
                project_uuid=identity.project_uuid,
                severity="info",
                payload={}
            ))
    
    # Step 2: Find CMP-only projects (not on GitHub)
    print("\n[STEP 2] Finding CMP-only projects...")
    
    cmp_only_count = 0
    for key, cmp_info in cmp_data.items():
        if key not in seen_keys:
            cmp_only_count += 1
            stats.cmp_only += 1
            # These are projects in CMP but not found in GitHub scan
            # Could be local-only, external, or planned projects
    
    print(f"  CMP-only projects: {cmp_only_count}")
    
    # Step 3: Build outputs
    print("\n[STEP 3] Generating outputs...")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    scan_result = IdentityScanResult(
        generated_at=timestamp,
        namespace_used=str(NAMESPACE_CMP),
        stats=stats,
        projects=projects
    )
    
    patch = IdentityPatch(
        generated_at=timestamp,
        dry_run=True,
        actions=actions
    )
    
    # Save outputs
    output_dir = get_omni_artifacts_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scan_path = output_dir / "scan.project_identity.json"
    with open(scan_path, 'w', encoding='utf-8') as f:
        json.dump(scan_result.model_dump(), f, indent=2)
    print(f"  Saved: {scan_path}")
    
    patch_path = output_dir / "project_identity.patch.json"
    with open(patch_path, 'w', encoding='utf-8') as f:
        json.dump(patch.model_dump(), f, indent=2)
    print(f"  Saved: {patch_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY] Phase A Reconciliation Complete")
    print("=" * 60)
    print(f"  Total projects: {stats.total}")
    print(f"  - From GitHub: {stats.from_github}")
    print(f"  - CMP-only: {stats.cmp_only}")
    print()
    print(f"  UUID Sources:")
    print(f"  - From master registry: {stats.has_uuid_from_master}")
    print(f"  - Minted (UUIDv5): {stats.needs_uuid_minted}")
    print()
    print(f"  CMP Status:")
    print(f"  - In CMP: {stats.in_cmp}")
    print(f"  - NOT in CMP (need to add): {stats.not_in_cmp}")
    print(f"  - Have local paths: {stats.has_local_path}")
    print()
    print(f"  Conflicts: {stats.conflicts}")
    print(f"  Patch has work: {patch.has_work}")
    print("=" * 60)
    
    # Victory banner when converged
    if not patch.has_work and stats.conflicts == 0:
        print()
        print("  ** CONVERGED: Identity stable. No actions required. **")
        print()
    
    return scan_result, patch


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase A Identity Reconciliation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    reconcile(verbose=args.verbose)
