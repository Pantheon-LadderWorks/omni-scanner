"""
Temporal Gap Analyzer - Comprehensive Git History Resurrection Intelligence

Contract: C-TOOLS-OMNI-SCANNER-001
Category: Phoenix (Git Resurrection)  
Pillar Integration: CartographyPillar (project paths), ConstitutionPillar (UUID validation)

Combines:
- Archive scanning (archive_scanner.py)
- Orphan detection (orphan_detector.py)
- Project registry matching
- Temporal gap analysis

Produces resurrection intelligence report:
- Which repos need resurrection
- Which archives match which repos
- Orphaned commits timeline
- Fast-forward vs manual merge decision
- Genesis canonization readiness

Usage:
    omni scan phoenix --full-report --archives="Downloads/" --workspace="Projects/"
    omni scan phoenix --temporal-gaps --out=resurrection_plan.json
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from omni.core.paths import get_infrastructure_root, should_skip_path
from omni.config.settings import get_governance_path

# Piggyback on existing scanners
from .archive_scanner import scan as archive_scan
from .orphan_detector import scan as orphan_scan


def _normalize_repo_name(name: str) -> str:
    """
    Normalize repository name for matching.
    
    Args:
        name: Repository name (from URL or folder)
        
    Returns:
        Normalized name (lowercase, - → _, .git removed)
    """
    name = name.lower()
    name = name.replace('.git', '')
    name = name.replace('-', '_')
    return name


def _match_archive_to_repo(archive_name: str, repo_name: str, remote_url: Optional[str] = None) -> float:
    """
    Calculate match confidence between archive and repo.
    
    Args:
        archive_name: Archive repository name
        repo_name: Current repository folder name
        remote_url: Optional remote URL for exact matching
        
    Returns:
        Confidence score (0.0-1.0)
    """
    if remote_url and archive_name in remote_url:
        return 1.0  # Exact match
    
    norm_archive = _normalize_repo_name(archive_name)
    norm_repo = _normalize_repo_name(repo_name)
    
    if norm_archive == norm_repo:
        return 0.95  # Very high confidence
    
    if norm_archive in norm_repo or norm_repo in norm_archive:
        return 0.7  # Substring match
    
    return 0.0  # No match


def _find_local_repos(base_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Find all local git repositories in given paths.
    
    Args:
        base_paths: List of paths to search
        
    Returns:
        List of repo metadata dicts
    """
    repos = []
    
    for base in base_paths:
        if not base.exists():
            continue
        
        # Find all .git folders
        for git_dir in base.rglob('.git'):
            if not git_dir.is_dir():
                continue
            
            repo_path = git_dir.parent
            
            if should_skip_path(repo_path):
                continue
            
            repos.append({
                "path": str(repo_path),
                "name": repo_path.name,
                "has_git": True
            })
    
    return repos


def scan(target: Path, **kwargs) -> Dict[str, Any]:
    """
    Perform comprehensive temporal gap analysis.
    
    Contract: C-TOOLS-OMNI-SCANNER-001 compliant
    Pillar Integration: CartographyPillar (via omni.core.paths)
    
    Args:
        target: Path to archives directory
        **kwargs: Scanner parameters
            - workspaces: List[str] - Workspace paths to scan for repos
            - full_report: bool - Generate detailed resurrection plan
            - out: Path - Output file for resurrection plan JSON
    
    Returns:
        Dict with:
            count: Number of repos needing resurrection
            items: List of resurrection targets
            metadata: Scanner info
            summary: Statistics
            resurrection_plan: Detailed execution plan
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "phoenix.temporal_gap",
            "version": "1.0.0",
            "description": "Comprehensive git history resurrection intelligence",
            "target": str(target),
            "timestamp": datetime.now().isoformat()
        },
        "summary": {
            "archives_found": 0,
            "repos_found": 0,
            "matched_pairs": 0,
            "orphaned_commits_total": 0,
            "resurrection_needed": 0,
            "fast_forward_possible": 0,
            "manual_merge_needed": 0,
            "no_local_repo": 0
        },
        "resurrection_plan": []
    }
    
    # Step 1: Scan archives
    print("🔍 Scanning archives...")
    archive_results = archive_scan(target, recursive=True)
    archives = archive_results["items"]
    results["summary"]["archives_found"] = len(archives)
    
    # Step 2: Find local repos
    print("🔍 Finding local repositories...")
    workspace_paths = kwargs.get('workspaces', [
        'C:\\Users\\kryst\\Projects',
        'C:\\Users\\kryst\\Infrastructure',
        'C:\\Users\\kryst\\Workspace'
    ])
    workspace_paths = [Path(p) for p in workspace_paths if Path(p).exists()]
    
    local_repos = _find_local_repos(workspace_paths)
    results["summary"]["repos_found"] = len(local_repos)
    
    # Step 3: Match archives to repos
    print("🔍 Matching archives to repositories...")
    for archive in archives:
        if "repo_name" not in archive:
            continue
        
        archive_name = archive["repo_name"]
        archive_path = Path(archive["zip_path"])
        
        # Find matching repo
        best_match = None
        best_confidence = 0.0
        
        for repo in local_repos:
            remote_url = archive.get("remote_url")
            confidence = _match_archive_to_repo(archive_name, repo["name"], remote_url)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = repo
        
        if best_match and best_confidence >= 0.7:
            results["summary"]["matched_pairs"] += 1
            
            # Check for orphaned commits
            repo_path = Path(best_match["path"])
            orphan_results = orphan_scan(archive_path, repo=repo_path)
            
            orphaned_count = orphan_results["count"]
            results["summary"]["orphaned_commits_total"] += orphaned_count
            
            if orphaned_count > 0:
                results["summary"]["resurrection_needed"] += 1
                
                merge_strategy = orphan_results["metadata"].get("merge_strategy", "unknown")
                if "fast-forward" in merge_strategy.lower():
                    results["summary"]["fast_forward_possible"] += 1
                else:
                    results["summary"]["manual_merge_needed"] += 1
                
                resurrection_target = {
                    "archive": archive["zip_file"],
                    "archive_path": archive["zip_path"],
                    "repo_name": archive_name,
                    "repo_path": str(repo_path),
                    "match_confidence": best_confidence,
                    "orphaned_commits": orphaned_count,
                    "merge_strategy": merge_strategy,
                    "orphaned_commit_details": orphan_results["items"],
                    "estimated_commits": archive.get("estimated_commits", 0),
                    "remote_url": archive.get("remote_url", ""),
                    "priority": "HIGH" if orphaned_count > 5 else "MEDIUM"
                }
                
                results["items"].append(resurrection_target)
                results["resurrection_plan"].append({
                    "step": len(results["resurrection_plan"]) + 1,
                    "action": "resurrect",
                    "archive": archive["zip_file"],
                    "target": str(repo_path),
                    "commits_to_restore": orphaned_count,
                    "method": "fast-forward" if "fast-forward" in merge_strategy.lower() else "manual",
                    "genesis_canonize": f"genesis canonize {repo_path} --domain=projects --type=repo"
                })
        else:
            # Archive has no matching local repo
            results["summary"]["no_local_repo"] += 1
            
            resurrection_target = {
                "archive": archive["zip_file"],
                "archive_path": archive["zip_path"],
                "repo_name": archive_name,
                "repo_path": None,
                "match_confidence": 0.0,
                "orphaned_commits": archive.get("estimated_commits", 0),
                "merge_strategy": "new_clone_needed",
                "priority": "LOW",
                "note": "No local repository found - may need fresh clone"
            }
            results["items"].append(resurrection_target)
    
    results["count"] = results["summary"]["resurrection_needed"]
    
    # Save resurrection plan if requested
    out_path = kwargs.get('out')
    if out_path:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Resurrection plan saved to: {out_file}")
    
    return results
