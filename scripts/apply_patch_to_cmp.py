#!/usr/bin/env python3
"""
Phase B: CMP Patch Applier

Applies project identity patches to CMP registry.
Runs in dry-run mode by default.

Usage:
    python apply_patch_to_cmp.py                    # Dry run
    python apply_patch_to_cmp.py --execute          # Actually apply
    python apply_patch_to_cmp.py --verbose          # Show details

Actions supported:
    - CMP_CREATE: Add new project to CMP
    - CMP_BACKFILL_UUID: Add UUID to existing project
    - NO_OP: Already in sync
    - CONFLICT_FREEZE: UUID conflict - manual review needed
"""

import json
import yaml
import sys
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from copy import deepcopy

# Fix Windows console encoding for emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add omni to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omni.config.settings import (
    get_cmp_registry_path,
    get_omni_artifacts_path,
)


@dataclass
class ApplyResult:
    """Result of applying a single patch action."""
    action_type: str
    project_key: str
    status: str  # "applied", "skipped", "error", "conflict"
    message: str
    changes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatchReport:
    """Summary of patch application."""
    timestamp: str
    dry_run: bool
    total_actions: int
    applied: int = 0
    skipped: int = 0
    errors: int = 0
    conflicts: int = 0
    results: List[ApplyResult] = field(default_factory=list)
    
    def add_result(self, result: ApplyResult):
        self.results.append(result)
        if result.status == "applied":
            self.applied += 1
        elif result.status == "skipped":
            self.skipped += 1
        elif result.status == "error":
            self.errors += 1
        elif result.status == "conflict":
            self.conflicts += 1
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "dry_run": self.dry_run,
            "summary": {
                "total": self.total_actions,
                "applied": self.applied,
                "skipped": self.skipped,
                "errors": self.errors,
                "conflicts": self.conflicts,
            },
            "results": [
                {
                    "action_type": r.action_type,
                    "project_key": r.project_key,
                    "status": r.status,
                    "message": r.message,
                    "changes": r.changes,
                }
                for r in self.results
            ]
        }


def load_patch() -> Dict:
    """Load the identity patch file."""
    patch_path = get_omni_artifacts_path() / "project_identity.patch.json"
    if not patch_path.exists():
        raise FileNotFoundError(f"Patch file not found: {patch_path}")
    
    with open(patch_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_cmp_registry() -> Dict:
    """Load CMP registry YAML."""
    cmp_path = get_cmp_registry_path()
    if not cmp_path.exists():
        raise FileNotFoundError(f"CMP registry not found: {cmp_path}")
    
    with open(cmp_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_cmp_registry(data: Dict, backup: bool = True):
    """Save CMP registry YAML."""
    cmp_path = get_cmp_registry_path()
    
    # Create backup in proper CMP backup folder
    if backup and cmp_path.exists():
        backup_folder = cmp_path.parent / "backup"
        backup_folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_folder / f"PANTHEON_PROJECT_REGISTRY.pre_phase_b_{timestamp}.yaml"
        import shutil
        shutil.copy(cmp_path, backup_path)
        print(f"[BACKUP] Created: {backup_path}")
    
    with open(cmp_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def find_project_in_cmp(cmp_data: Dict, project_key: str) -> Optional[Dict]:
    """Find a project in CMP by project_key (checking primary_repo URL)."""
    for proj in cmp_data.get('projects', []):
        primary_repo = proj.get('primary_repo', '')
        # Convert URL to project_key format for comparison
        if primary_repo:
            # https://github.com/owner/repo -> github:owner/repo
            if 'github.com/' in primary_repo:
                parts = primary_repo.rstrip('/').split('github.com/')[-1].lower()
                cmp_key = f"github:{parts}"
                if cmp_key == project_key.lower():
                    return proj
    return None


def apply_cmp_create(
    action: Dict,
    cmp_data: Dict,
    scan_data: Dict,
    dry_run: bool
) -> ApplyResult:
    """Apply CMP_CREATE action - add new project."""
    project_key = action['project_key']
    project_uuid = action['project_uuid']
    payload = action.get('payload', {})
    
    # Check if already exists
    existing = find_project_in_cmp(cmp_data, project_key)
    if existing:
        return ApplyResult(
            action_type="CMP_CREATE",
            project_key=project_key,
            status="skipped",
            message=f"Project already exists: {existing.get('display_name')}",
        )
    
    # Find full project data from scan
    scan_project = None
    for proj in scan_data.get('projects', []):
        if proj['project_key'] == project_key:
            scan_project = proj
            break
    
    if not scan_project:
        return ApplyResult(
            action_type="CMP_CREATE",
            project_key=project_key,
            status="error",
            message="Project not found in scan data",
        )
    
    # Build new CMP entry
    new_entry = {
        'display_name': scan_project.get('name', payload.get('name', 'Unknown')),
        'status': 'active',
        'classification': scan_project.get('classification', 'github_only_project'),
        'primary_repo': scan_project.get('github_url'),
        'uuid': project_uuid,
        'tags': ['auto-created', 'phase-b'],
    }
    
    # Add description if available
    if scan_project.get('description'):
        new_entry['description'] = scan_project['description']
    
    # Add local paths if available
    if scan_project.get('local_paths'):
        new_entry['local_paths'] = scan_project['local_paths']
    
    if not dry_run:
        cmp_data.setdefault('projects', []).append(new_entry)
    
    return ApplyResult(
        action_type="CMP_CREATE",
        project_key=project_key,
        status="applied",
        message=f"Created project: {new_entry['display_name']}",
        changes={"new_entry": new_entry}
    )


def apply_conflict_freeze(action: Dict) -> ApplyResult:
    """Handle CONFLICT_FREEZE - log for manual review."""
    return ApplyResult(
        action_type="CONFLICT_FREEZE",
        project_key=action['project_key'],
        status="conflict",
        message=f"UUID conflict requires manual review: {action.get('payload', {}).get('conflict', 'unknown')}",
        changes={"conflict_details": action.get('payload', {})}
    )


def apply_patch(
    patch: Dict,
    cmp_data: Dict,
    scan_data: Dict,
    dry_run: bool = True,
    verbose: bool = False
) -> PatchReport:
    """Apply all patch actions to CMP data."""
    
    actions = patch.get('actions', [])
    report = PatchReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        dry_run=dry_run,
        total_actions=len(actions),
    )
    
    for action in actions:
        action_type = action.get('action_type', 'UNKNOWN')
        project_key = action.get('project_key', 'unknown')
        
        if verbose:
            print(f"  [{action_type}] {project_key}")
        
        if action_type == "CMP_CREATE":
            result = apply_cmp_create(action, cmp_data, scan_data, dry_run)
        elif action_type == "CONFLICT_FREEZE":
            result = apply_conflict_freeze(action)
        elif action_type == "NO_OP":
            result = ApplyResult(
                action_type="NO_OP",
                project_key=project_key,
                status="skipped",
                message="Already in sync",
            )
        else:
            result = ApplyResult(
                action_type=action_type,
                project_key=project_key,
                status="skipped",
                message=f"Unhandled action type: {action_type}",
            )
        
        report.add_result(result)
        
        if verbose and result.status != "skipped":
            print(f"    → {result.status}: {result.message}")
    
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase B: Apply identity patch to CMP")
    parser.add_argument("--execute", action="store_true", help="Actually apply changes (default: dry-run)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    print("=" * 60)
    print("[PHASE B] CMP Patch Applier")
    print(f"Mode: {'DRY RUN' if dry_run else '⚠️  EXECUTE MODE'}")
    print("=" * 60)
    
    # Load data
    print("\n[LOAD] Loading data sources...")
    
    patch = load_patch()
    print(f"  Patch actions: {len(patch.get('actions', []))}")
    
    cmp_data_original = load_cmp_registry()
    cmp_data = deepcopy(cmp_data_original)  # Work on copy
    print(f"  CMP projects: {len(cmp_data.get('projects', []))}")
    
    # Load scan for full project data
    scan_path = get_omni_artifacts_path() / "scan.project_identity.json"
    with open(scan_path, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
    print(f"  Scan projects: {len(scan_data.get('projects', []))}")
    
    # Apply patch
    print("\n[APPLY] Processing patch actions...")
    report = apply_patch(patch, cmp_data, scan_data, dry_run=dry_run, verbose=args.verbose)
    
    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print("=" * 60)
    print(f"  Total actions: {report.total_actions}")
    print(f"  Applied: {report.applied}")
    print(f"  Skipped: {report.skipped}")
    print(f"  Errors: {report.errors}")
    print(f"  Conflicts: {report.conflicts}")
    
    # Show what would be created
    creates = [r for r in report.results if r.action_type == "CMP_CREATE" and r.status == "applied"]
    if creates:
        print(f"\n  Projects {'to create' if dry_run else 'created'}:")
        for r in creates:
            print(f"    + {r.changes.get('new_entry', {}).get('display_name', r.project_key)}")
    
    # Save report
    output_dir = get_omni_artifacts_path()
    report_path = output_dir / "cmp_patch_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\n  Report saved: {report_path}")
    
    # Save modified CMP if not dry-run
    if not dry_run and report.applied > 0:
        save_cmp_registry(cmp_data)
        print(f"\n  ✅ CMP registry updated!")
    elif dry_run and report.applied > 0:
        print(f"\n  ⚠️  Run with --execute to apply {report.applied} changes")
    
    print("=" * 60)
    
    return report


if __name__ == "__main__":
    main()
