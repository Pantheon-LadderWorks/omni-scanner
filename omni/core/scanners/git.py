"""
Git Status Scanner - Federation Repo Health

Usage:
    omni scan --scanners=git .
    omni scan --scanners=git /path/to/federation

Detects:
    - Uncommitted changes
    - Un-pushed commits  
    - Behind remote
    - Branch information
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List

from omni.core.paths import should_skip_path


def _find_git_repos(target: Path) -> List[Path]:
    """Find all git repositories under target."""
    repos = []
    
    for item in target.rglob(".git"):
        # Skip if:
        # 1. Not a directory (could be a .git file in submodules)
        # 2. Parent path contains .git (nested .git directory - cursed)
        # 3. Should be skipped by federation cartography
        if not item.is_dir():
            continue
        
        repo_path = item.parent
        
        # Skip inception: .git inside .git
        if ".git" in str(repo_path.relative_to(target) if repo_path != target else Path(".")):
            continue
            
        if not should_skip_path(repo_path):
            repos.append(repo_path)
    
    return repos


def _get_repo_status(repo_path: Path) -> Dict[str, Any]:
    """Get git status for a single repo."""
    try:
        # Get branch name
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        # Get uncommitted changes count
        status_output = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        changes = len(status_output.split("\n")) if status_output else 0
        
        # Get ahead/behind counts
        try:
            ahead = int(subprocess.run(
                ["git", "rev-list", "--count", "@{u}..HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            ).stdout.strip() or "0")
        except:
            ahead = 0
            
        try:
            behind = int(subprocess.run(
                ["git", "rev-list", "--count", "HEAD..@{u}"],
                cwd=repo_path,
                capture_output=True,
                text=True
            ).stdout.strip() or "0")
        except:
            behind = 0
        
        # Determine health status
        if changes == 0 and ahead == 0 and behind == 0:
            health = "clean"
        elif changes > 0 and ahead > 0:
            health = "dirty+unpushed"
        elif changes > 0:
            health = "dirty"
        elif ahead > 0:
            health = "unpushed"
        elif behind > 0:
            health = "behind"
        else:
            health = "unknown"
        
        return {
            "repo": repo_path.name,
            "path": str(repo_path),
            "branch": branch,
            "changes": changes,
            "ahead": ahead,
            "behind": behind,
            "health": health
        }
        
    except Exception as e:
        return {
            "repo": repo_path.name,
            "path": str(repo_path),
            "branch": "?",
            "changes": -1,
            "ahead": -1,
            "behind": -1,
            "health": "error",
            "error": str(e)
        }


def scan(target: Path) -> Dict[str, Any]:
    """
    Scan for git repositories and their status.
    
    Returns: {
        "count": N,
        "items": [repo_statuses],
        "summary": {...}
    }
    """
    target_path = Path(target).resolve()
    
    # Find all git repos
    repos = _find_git_repos(target_path)
    
    # Get status for each
    items = []
    for repo in repos:
        status = _get_repo_status(repo)
        items.append(status)
    
    # Sort by health priority (dirty first, then unpushed, then behind)
    health_priority = {
        "dirty+unpushed": 0,
        "dirty": 1,
        "unpushed": 2,
        "behind": 3,
        "error": 4,
        "clean": 5,
        "unknown": 6
    }
    items.sort(key=lambda x: (health_priority.get(x["health"], 99), -x.get("changes", 0)))
    
    # Generate summary
    by_health = {}
    total_changes = 0
    total_ahead = 0
    total_behind = 0
    
    for item in items:
        health = item["health"]
        by_health[health] = by_health.get(health, 0) + 1
        total_changes += max(0, item.get("changes", 0))
        total_ahead += max(0, item.get("ahead", 0))
        total_behind += max(0, item.get("behind", 0))
    
    return {
        "count": len(items),
        "items": items,
        "summary": {
            "by_health": by_health,
            "total_uncommitted_changes": total_changes,
            "total_unpushed_commits": total_ahead,
            "total_behind_commits": total_behind,
            "needs_attention": len([i for i in items if i["health"] not in ("clean", "unknown")])
        }
    }
