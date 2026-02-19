"""
File Utility Library
====================
Standard logic for file system traversal and exclusion.
Prevents "piggybacking" of basic file walking logic across scanners.
"""
from pathlib import Path
from typing import List, Generator, Optional, Set

DEFAULT_EXCLUDES = {
    '__pycache__', '.git', '.venv', 'venv', 'node_modules', 
    'dist', 'build', 'eggs', '.eggs', '*.egg-info',
    'archive', '.pytest_cache', '.vscode', '.idea'
}

def is_excluded(path: Path, excludes: Optional[Set[str]] = None) -> bool:
    """Check if a path matches exclusion patterns."""
    exclude_set = excludes or DEFAULT_EXCLUDES
    parts = set(path.parts)
    # Direct match in path parts
    if not exclude_set.isdisjoint(parts):
        return True
    # Pattern match (simplified) - if needed we can add fnmatch
    return False

def walk_project(
    root: Path, 
    extensions: Optional[List[str]] = None, 
    excludes: Optional[Set[str]] = None
) -> Generator[Path, None, None]:
    """
    Walk a directory tree yielding paths that match criteria.
    
    Args:
        root: Root directory to start scan
        extensions: List of file extensions to include (e.g. ['.py', '.yaml'])
                    If None, includes all files.
        excludes: Set of directory names to exclude. 
                  If None, uses DEFAULT_EXCLUDES.
    
    Yields:
        Path objects for matching files.
    """
    exclude_set = excludes or DEFAULT_EXCLUDES
    
    # Normalize extensions
    ext_set = set(extensions) if extensions else None
    
    for path in root.rglob("*"):
        if path.is_dir():
            continue
            
        # Check exclusions
        if is_excluded(path, exclude_set):
            continue
            
        # Check extensions
        if ext_set and path.suffix not in ext_set:
            continue
            
        yield path
