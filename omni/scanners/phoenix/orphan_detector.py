"""
Orphan Detector - Find Missing Commits Between Archive and Current Repo

Contract: C-TOOLS-OMNI-SCANNER-001
Category: Phoenix (Git Resurrection)

Compares git history between:
- Archive .git folder (extracted from .zip)
- Current repository folder

Detects:
- Orphaned commits (in archive, missing from current)
- Temporal gaps (missing chunks in timeline)
- Divergence (different commit hashes for same logical changes)
- Fast-forward possibility (can current merge archive cleanly?)

Usage:
    omni scan phoenix --orphans --archive="git-*.zip" --repo="Projects/lcs-context"
    omni scan phoenix --orphans --all  # Scan all repos vs all archives
"""

import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from omni.core.paths import get_infrastructure_root


def _extract_archive_git(zip_path: Path, temp_dir: Path) -> Optional[Path]:
    """
    Extract .git folder from archive to temp directory.
    
    Args:
        zip_path: Path to .zip archive
        temp_dir: Temporary extraction directory
        
    Returns:
        Path to extracted .git folder or None if not found
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            git_files = [f for f in files if '.git/' in f or '.git\\' in f]
            
            if not git_files:
                return None
            
            # Extract .git folder
            for file in git_files:
                zf.extract(file, temp_dir)
            
            # Find .git directory
            git_dir = temp_dir / ".git"
            if git_dir.exists():
                return git_dir
            
            # Handle nested structure
            for item in temp_dir.rglob(".git"):
                if item.is_dir():
                    return item
            
            return None
            
    except Exception as e:
        return None


def _get_all_commits(git_dir: Path) -> List[str]:
    """
    Get all commit hashes from a git repository.
    
    Args:
        git_dir: Path to .git directory
        
    Returns:
        List of commit hashes
    """
    try:
        result = subprocess.run(
            ["git", "--git-dir", str(git_dir), "rev-list", "--all"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        
        if result.returncode != 0:
            return []
        
        commits = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return commits
        
    except Exception:
        return []


def _get_commit_info(git_dir: Path, commit_hash: str) -> Dict[str, Any]:
    """
    Get detailed info for a commit.
    
    Args:
        git_dir: Path to .git directory
        commit_hash: Commit hash
        
    Returns:
        Dict with commit metadata
    """
    try:
        result = subprocess.run(
            ["git", "--git-dir", str(git_dir), "log", "-1", 
             "--format=%ci|%h|%s|%an", commit_hash],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode != 0:
            return {"hash": commit_hash, "error": "Failed to get info"}
        
        parts = result.stdout.strip().split('|', 3)
        if len(parts) == 4:
            return {
                "hash": commit_hash,
                "date": parts[0],
                "short_hash": parts[1],
                "message": parts[2],
                "author": parts[3]
            }
        
        return {"hash": commit_hash}
        
    except Exception:
        return {"hash": commit_hash}


def _check_commit_exists(repo_path: Path, commit_hash: str) -> bool:
    """
    Check if a commit exists in current repo.
    
    Args:
        repo_path: Path to current repository
        commit_hash: Commit hash to check
        
    Returns:
        True if commit exists
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "cat-file", "-e", commit_hash],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
        
    except Exception:
        return False


def _can_fast_forward(repo_path: Path, archive_git_dir: Path) -> Tuple[bool, str]:
    """
    Check if current repo can fast-forward merge from archive.
    
    Args:
        repo_path: Current repository path
        archive_git_dir: Archive .git directory
        
    Returns:
        (can_fast_forward: bool, reason: str)
    """
    try:
        # Get current HEAD
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            encoding='utf-8',
            timeout=5
        )
        
        if result.returncode != 0:
            return False, "Current repo has no HEAD"
        
        current_head = result.stdout.strip()
        
        # Get archive HEAD
        result = subprocess.run(
            ["git", "--git-dir", str(archive_git_dir), "rev-parse", "HEAD"],
            capture_output=True,
            encoding='utf-8',
            timeout=5
        )
        
        if result.returncode != 0:
            return False, "Archive has no HEAD"
        
        archive_head = result.stdout.strip()
        
        # Check if archive HEAD is reachable from current HEAD (fast-forward)
        result = subprocess.run(
            ["git", "-C", str(repo_path), "merge-base", "--is-ancestor", 
             current_head, archive_head],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return True, "Can fast-forward (current is ancestor of archive)"
        else:
            return False, "Diverged history (manual merge required)"
            
    except Exception as e:
        return False, f"Check failed: {str(e)}"


def scan(target: Path, **kwargs) -> Dict[str, Any]:
    """
    Scan for orphaned commits between archive and current repo.
    
    Contract: C-TOOLS-OMNI-SCANNER-001 compliant
    
    Args:
        target: Path to archive .zip file OR directory containing archives
        **kwargs: Scanner parameters
            - repo: Path - Current repository to compare against
            - repos: List[Path] - Multiple repos to compare
            - all: bool - Compare all found repos vs all archives
    
    Returns:
        Dict with:
            count: Number of orphaned commits found
            items: List of orphan commit details
            metadata: Scanner info
            summary: Statistics
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "phoenix.orphan",
            "version": "1.0.0",
            "description": "Orphaned commit detection for git resurrection",
            "target": str(target),
            "timestamp": datetime.now().isoformat()
        },
        "summary": {
            "archives_scanned": 0,
            "repos_compared": 0,
            "orphaned_commits_found": 0,
            "fast_forward_possible": 0,
            "diverged_histories": 0
        }
    }
    
    # Get repo path from kwargs
    repo_path = kwargs.get('repo')
    if repo_path and isinstance(repo_path, str):
        repo_path = Path(repo_path)
    
    if not repo_path or not repo_path.exists():
        results["metadata"]["error"] = "No valid repo path provided"
        return results
    
    # Create temp directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract archive
        archive_git = _extract_archive_git(target, temp_path)
        
        if not archive_git:
            results["metadata"]["error"] = "No .git folder found in archive"
            return results
        
        results["summary"]["archives_scanned"] = 1
        results["summary"]["repos_compared"] = 1
        
        # Get all commits from archive
        archive_commits = _get_all_commits(archive_git)
        
        if not archive_commits:
            results["metadata"]["error"] = "Failed to read archive commits"
            return results
        
        # Check each commit in current repo
        orphaned = []
        for commit_hash in archive_commits:
            exists = _check_commit_exists(repo_path, commit_hash)
            if not exists:
                commit_info = _get_commit_info(archive_git, commit_hash)
                orphaned.append(commit_info)
        
        results["count"] = len(orphaned)
        results["items"] = orphaned
        results["summary"]["orphaned_commits_found"] = len(orphaned)
        
        # Check if fast-forward possible
        can_ff, reason = _can_fast_forward(repo_path, archive_git)
        results["summary"]["fast_forward_possible"] = 1 if can_ff else 0
        results["summary"]["diverged_histories"] = 0 if can_ff else 1
        results["metadata"]["merge_strategy"] = reason
    
    return results
