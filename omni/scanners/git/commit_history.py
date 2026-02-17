"""
Git Commit History Scanner - PHOENIX RESURRECTION EVIDENCE
===========================================================

Captures complete commit history from git repositories and writes to registry.
Each repository gets its own commit history file in:
    governance/registry/commits/{repo_name}_commit_history.json

Usage:
    omni scan --scanners=commit-history .                   # Single repo
    omni scan --all --scanners=commit-history              # All registered repos
    omni scan --scanners=commit-history --rebuild-registry # Rebuild all commit histories

This scanner is a thin wrapper around omni.core.commit_history_builder.CommitHistoryBuilder.
The builder contains the core logic; the scanner provides CLI integration.

Author: Oracle (GitHub Copilot) + The Architect (Kryssie)
Date: February 12, 2026
Law: Charter V1.2 compliant - Federation pattern only
"""

from pathlib import Path
from typing import Dict, List
import logging

# Import builder from builders (where the real logic lives)
from omni.builders.commit_history_builder import CommitHistoryBuilder

logger = logging.getLogger("Omni.Scanners.Git.CommitHistory")


def scan(paths: List[Path], **kwargs) -> Dict:
    """
    Scanner entry point called by Omni CLI.
    
    Args:
        paths: List of paths to scan (repos or directories)
        **kwargs: Additional scan options:
            - rebuild_registry: bool - Rebuild all repo commit histories
            
    Returns:
        Scan results summary
    """
    rebuild_registry = kwargs.get('rebuild_registry', False)
    
    # Initialize builder
    try:
        builder = CommitHistoryBuilder()
    except Exception as e:
        logger.error(f"Failed to initialize CommitHistoryBuilder: {e}")
        return {"status": "error", "message": str(e)}
    
    if rebuild_registry:
        # Rebuild all registered repos from inventory
        logger.info("🔥 Rebuilding commit history registry for all repos...")
        results = builder.build_all()
        
        return {
            "status": "rebuild_complete",
            "total": len(results),
            "successful": sum(1 for v in results.values() if v),
            "results": results
        }
    
    else:
        # Scan provided paths
        results = {}
        
        for path in paths:
            path = Path(path).resolve()
            
            # Check if it's a git repo
            if (path / '.git').exists():
                success = builder.build_single(path)
                results[path.name] = success
            else:
                # Try to find git repos in subdirectories
                for git_dir in path.rglob('.git'):
                    if git_dir.is_dir():
                        repo_path = git_dir.parent
                        success = builder.build_single(repo_path)
                        results[repo_path.name] = success
        
        successful = sum(1 for v in results.values() if v)
        
        return {
            "status": "scan_complete",
            "total": len(results),
            "successful": successful,
            "results": results
        }
