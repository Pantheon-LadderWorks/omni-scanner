"""
Git Status Scanner - Federation Repo Health

Usage:
    omni scan --scanners=git .
    omni scan --scanners=git /path/to/federation
    omni scan --scanners=git --github  # Use gh CLI to scan remote repos

Detects:
    - Uncommitted changes
    - Un-pushed commits  
    - Behind remote
    - Branch information
    
GitHub Mode (--github flag):
    - Fetches all repos from authenticated gh session
    - Compares with local clones
    - Auto-updates governance/registry/git_repos/repo_inventory.json
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from omni.core.paths import should_skip_path
from omni.config.settings import get_governance_path

# Paths via settings (Federation Heart integration)
REGISTRY_PATH = get_governance_path("registry/git_repos/repo_inventory.json")


def _fetch_github_repos(owner: Optional[str] = None, limit: int = 500) -> List[Dict]:
    """
    Fetch repos from GitHub using gh CLI.
    
    Args:
        owner: GitHub username/org. If None, fetches authenticated user's repos.
        limit: Maximum repos to fetch.
        
    Returns:
        List of repo dicts with name, url, description, visibility, updatedAt, owner
    """
    try:
        cmd = [
            "gh", "repo", "list",
        ]
        
        if owner:
            cmd.append(owner)
            
        cmd.extend([
            "--json", "name,url,description,visibility,updatedAt,owner",
            "--limit", str(limit)
        ])
        
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
        
        if result.returncode != 0:
            return []
            
        repos = json.loads(result.stdout)
            
        repos = json.loads(result.stdout)
        return repos
        
    except Exception as e:
        print(f"[WARN] Failed to fetch repos from {owner or 'user'}: {e}")
        return []


def _get_user_orgs() -> List[str]:
    """Get all orgs the authenticated user belongs to."""
    try:
        result = subprocess.run(
            ["gh", "api", "user/orgs", "--jq", ".[].login"],
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            return []
            
        orgs = [org.strip() for org in result.stdout.strip().split("\n") if org.strip()]
        return orgs
        
    except Exception:
        return []


def _load_registry() -> List[Dict]:
    """Load existing repo inventory registry."""
    if not REGISTRY_PATH.exists():
        return []
        
    try:
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_registry(repos: List[Dict]):
    """Save updated repo inventory registry."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(repos, f, indent=4, ensure_ascii=False)


def scan_github(update_registry: bool = True) -> Dict[str, Any]:
    """
    Scan all repos from GitHub and compare with local/registry.
    
    Returns scan results including:
        - All GitHub repos (user + orgs)
        - Comparison with existing registry
        - New repos not in registry
        - Orphaned registry entries
    """
    from omni.config.settings import get_git_config
    
    config = get_git_config()
    
    print("[GITHUB] Fetching repos via gh CLI...")
    
    # Fetch user repos
    # Use config['users'] if defined, otherwise default to authenticated user
    target_users = config.get("users", [])
    if not target_users:
        # Default behavior: authenticated user
        user_repos = _fetch_github_repos()
        print(f"  [OK] Authenticated User: {len(user_repos)} repos")
    else:
        user_repos = []
        for user in target_users:
            repos = _fetch_github_repos(owner=user)
            user_repos.extend(repos)
            print(f"  [OK] User {user}: {len(repos)} repos")
    
    # Fetch org repos
    # Use config['orgs'] if defined, otherwise auto-detect
    target_orgs = config.get("orgs", [])
    if not target_orgs:
        target_orgs = _get_user_orgs()
        
    org_repos = []
    for org in target_orgs:
        repos = _fetch_github_repos(owner=org)
        org_repos.extend(repos)
        print(f"  [OK] Org {org}: {len(repos)} repos")
    
    # Combine and dedupe by URL
    all_github_repos = []
    seen_urls = set()
    
    for repo in user_repos + org_repos:
        url = repo.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            all_github_repos.append(repo)
    
    print(f"  [TOTAL] {len(all_github_repos)} unique GitHub repos")
    
    # Load existing registry
    existing_registry = _load_registry()
    existing_urls = {r.get('url', '') for r in existing_registry}
    
    # Find new repos (in GitHub but not in registry)
    new_repos = [r for r in all_github_repos if r.get('url') not in existing_urls]
    
    # Find orphaned registry entries (in registry but not in GitHub)
    github_urls = {r.get('url') for r in all_github_repos}
    orphaned = [r for r in existing_registry if r.get('url') not in github_urls]
    
    # Build updated registry - GitHub is authoritative, replace entirely
    # This ensures no duplicates and removes orphaned entries
    if update_registry:
        # Dedupe the fresh GitHub data (should already be clean, but safety first)
        seen_urls = set()
        deduped_repos = []
        for repo in all_github_repos:
            url = repo.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped_repos.append(repo)
        
        _save_registry(deduped_repos)
        print(f"  [UPDATED] Registry now has {len(deduped_repos)} repos (was {len(existing_registry)})")
    
    return {
        "count": len(all_github_repos),
        "items": all_github_repos,
        "registry": {
            "path": str(REGISTRY_PATH),
            "existing_count": len(existing_registry),
            "new_repos": [r.get('name') for r in new_repos],
            "new_count": len(new_repos),
            "orphaned_repos": [r.get('name') for r in orphaned],
            "orphaned_count": len(orphaned),
            "updated": update_registry and len(new_repos) > 0
        },
        "by_visibility": {
            "PUBLIC": len([r for r in all_github_repos if r.get('visibility') == 'PUBLIC']),
            "PRIVATE": len([r for r in all_github_repos if r.get('visibility') == 'PRIVATE']),
        },
        "orgs_scanned": orgs
    }



from omni.scanners.git.git_util import get_remote_url, find_git_repos


def scan_local_paths(scan_roots: Optional[List[Path]] = None) -> Dict[str, str]:
    """
    Scan local filesystem for git repos and map GitHub URLs to local paths.
    
    Scans all 4 workspaces: Infrastructure, Workspace, Deployment, Projects.
    
    Args:
        scan_roots: Directories to scan. If None, uses all workspaces via CartographyPillar.
        
    Returns:
        Dict of { 'github_url_lowercase': 'local_path' }
    """
    if scan_roots is None:
        # Use settings shim to get all workspace roots (respects USER_MANIFEST_V1.yaml)
        try:
            from omni.config.settings import get_all_workspaces as _get_workspaces
            scan_roots = _get_workspaces()
            
        except ImportError:
            # Fallback if Heart not available
            from omni.config import settings
            scan_roots = [settings.get_infrastructure_root()]
    
    url_to_path = {}
    
    for root in scan_roots:
        if not root.exists():
            continue
            
        repos = find_git_repos(root)
        
        for repo_path in repos:
            remote_url = get_remote_url(repo_path)
            if remote_url:
                # Store the mapping (first found wins)
                if remote_url not in url_to_path:
                    url_to_path[remote_url] = str(repo_path)
    
    return url_to_path


def _get_repo_status(repo_path: Path) -> Dict[str, Any]:
    """Get git status for a single repo."""
    try:
        # Get branch name
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        ).stdout.strip()
        
        # Get uncommitted changes count
        status_output = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        ).stdout.strip()
        
        changes = len(status_output.split("\n")) if status_output else 0
        
        # Get ahead/behind counts
        try:
            ahead = int(subprocess.run(
                ["git", "rev-list", "--count", "@{u}..HEAD"],
                cwd=repo_path,
                capture_output=True,
                encoding='utf-8',
                errors='replace'
            ).stdout.strip() or "0")
        except:
            ahead = 0
            
        try:
            behind = int(subprocess.run(
                ["git", "rev-list", "--count", "HEAD..@{u}"],
                cwd=repo_path,
                capture_output=True,
                encoding='utf-8',
                errors='replace'
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


def scan(target: Path, github: bool = False, update_registry: bool = True) -> Dict[str, Any]:
    """
    Scan for git repositories and their status.
    
    Args:
        target: Directory to scan for local git repos.
        github: If True, use gh CLI to scan all GitHub repos instead of local.
        update_registry: If True (with github=True), auto-update repo_inventory.json.
    
    Returns: {
        "count": N,
        "items": [repo_statuses],
        "summary": {...}
    }
    """
    # GitHub mode: fetch from gh CLI
    if github:
        return scan_github(update_registry=update_registry)
    target_path = Path(target).resolve()
    
    # Find all git repos
    repos = find_git_repos(target_path)
    
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
