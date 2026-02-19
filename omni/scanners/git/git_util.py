"""
Git Utility Library
===================
Shared logic for git operations to prevent duplication across scanners.
"""
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Tuple, Dict

def run_git_command(
    repo_path: Path, 
    command: List[str], 
    timeout: int = 30
) -> Tuple[Optional[str], Optional[str]]:
    """
    Run a git command in the repository.
    
    Args:
        repo_path: Path to git repo
        command: List of arguments (after 'git')
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (stdout, stderr) or (None, error_message)
    """
    try:
        # Check if git is installed
        if not shutil.which("git"):
            return None, "Git executable not found in PATH"

        result = subprocess.run(
            ['git'] + command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            return result.stdout.strip(), None
        else:
            return None, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return None, "Command timeout"
    except Exception as e:
        return None, str(e)

def get_remote_url(repo_path: Path) -> Optional[str]:
    """
    Get the remote origin URL for a git repo.
    Returns normalized GitHub URL (https) or None.
    """
    stdout, _ = run_git_command(repo_path, ["remote", "get-url", "origin"])
    if not stdout:
        return None
        
    url = stdout.strip()
    
    # Normalize git@github.com:owner/repo.git to https://github.com/owner/repo
    if url.startswith("git@github.com:"):
        url = url.replace("git@github.com:", "https://github.com/")
    
    # Strip .git suffix
    if url.endswith(".git"):
        url = url[:-4]
        
    # Only return GitHub URLs (for now, adaptable later)
    if "github.com" in url:
        return url.lower()
        
    return None

def find_git_repos(root: Path) -> List[Path]:
    """
    Find all git repositories under target.
    Skips nested .git directories.
    """
    repos = []
    # Use standard excludes from omni.lib.files if available, else basic list
    try:
        from omni.lib.files import is_excluded
    except ImportError:
        is_excluded = lambda p: False

    for item in root.rglob(".git"):
        if not item.is_dir():
            continue
            
        repo_path = item.parent
        
        # Check standard excludes for the PARENT path
        if is_excluded(repo_path):
             continue

        # Skip inception: .git inside .git (very rare but possible in messy worktrees)
        try:
            # simple check: if any part of the relative path is .git (except the end)
            rel = repo_path.relative_to(root)
            if ".git" in rel.parts:
                continue
        except ValueError:
            pass

        repos.append(repo_path)
    
    return repos
