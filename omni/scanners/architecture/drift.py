"""
Drift Scanner (Architecture Category)
=====================================
The Reality Check. Compares the Map (Registry) against the Territory (Filesystem).

" The map is not the territory... but it should be close." - The Cartographer

Authority:
    - C-HEART-CARTOGRAPHY-001 (Registry is Truth)
    - C-OMNI-DISCOVERY-CENSUS-001 (Filesystem is Reality)

Capabilities:
    - Detects "Ghost Projects" (In Registry, missing on disk)
    - Detects "Rogue Projects" (On disk, missing in Registry)
    - Validates Workspace consistency

Usage:
    omni scan --scanners=architecture.drift .
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Set

from omni.config import settings

def _load_registry_projects() -> Dict[str, Path]:
    """Load the Expected State from the Registry."""
    # Use standard accessor
    if hasattr(settings, 'get_project_registry_path'):
        registry_path = settings.get_project_registry_path()
    else:
        # Fallback if settings is old/mocked
        registry_path = Path("projects.yaml")

    if not registry_path or not registry_path.exists():
        return {}

    try:
        content = registry_path.read_text(encoding='utf-8')
        data = {}
        
        # Handle Markdown with Frontmatter
        if registry_path.suffix.lower() == '.md':
            import re
            match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                data = yaml.safe_load(match.group(1))
        # Handle Plain YAML
        elif registry_path.suffix.lower() in ('.yaml', '.yml'):
            data = yaml.safe_load(content)
            
        projects = {}
        
        for proj in data.get('projects', []):
            pid = proj.get('project_id')
            # Prefer local paths
            paths = proj.get('local_paths', [])
            if pid and paths:
                projects[pid] = paths[0]
                
        return projects
    except Exception as e:
        print(f"Error loading registry {registry_path}: {e}")
        return {}

def _scan_territory(roots: List[Path]) -> Dict[str, Path]:
    """
    Scan the Actual State from the Filesystem.
    
    Heuristic: A folder is a 'Project' if it has:
    - .git/
    - package.json
    - pyproject.toml
    - README.md (weak signal, maybe ignore)
    """
    actual_projects = {}
    
    # Markers that signify "This is a Project"
    MARKERS = {'.git', 'package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod'}
    
    start_dirs = roots if roots else [Path.cwd()]
    
    for root in start_dirs:
        if not root.exists(): continue
        
        # Shallow walk (depth 2-3) to find project roots
        # We don't want to scan node_modules
        for path in root.rglob("*"):
            if path.is_dir():
                # Skip massive ignore dirs
                if any(x in path.parts for x in {'.git', 'node_modules', 'dist', 'build', '.venv'}):
                    continue
                    
                # Check for markers
                is_project = False
                for marker in MARKERS:
                    if (path / marker).exists():
                        is_project = True
                        break
                
                if is_project:
                    # Use folder name as generic ID if we can't be smarter
                    pid = path.name
                    actual_projects[str(path)] = pid
                    
    return actual_projects

def scan(target: Path, **options) -> Dict[str, Any]:
    """
    Scan for Architectural Drift.
    
    Args:
        target: Root to scan (ignored if settings.get_all_workspaces() is available)
    """
    # 1. Get the Map (Registry)
    expected_projects = _load_registry_projects()
    
    # 2. Get the Territory (Filesystem)
    # Use configured workspaces if available, else target
    try:
        workspaces = settings.get_all_workspaces()
    except Exception:
        workspaces = [target]
        
    actual_projects_map = _scan_territory(workspaces)
    # Reverse map for easier lookup: Path -> ID
    actual_paths = set(str(Path(p).resolve()) for p in actual_projects_map.keys())
    
    # 3. Compare
    # Normalize expected paths to absolute strings for comparison
    # This is tricky because Registry might have relative paths.
    # We'll try to match by Folder Name for fuzzy matching if exact path fails.
    
    ghosts = [] # In Registry, Missing on Disk
    rogues = [] # On Disk, Missing in Registry
    matches = []
    
    # Check Ghosts
    infra_root = settings.get_infrastructure_root()
    
    for pid, rel_path in expected_projects.items():
        # Try to resolve absolute path
        if infra_root:
            full_path = (infra_root / rel_path).resolve()
        else:
            full_path = Path(rel_path).resolve()
            
        if not full_path.exists():
            ghosts.append({
                "id": pid,
                "expected_at": str(full_path),
                "status": "missing_on_disk"
            })
        else:
            matches.append(pid)

    # Check Rogues (This is harder - requires checking if actual path key matches any expected project)
    # Simplified: If the actual folder name isn't in any expected project ID or path
    
    expected_ids = set(expected_projects.keys())
    
    for path_str, pid_guess in actual_projects_map.items():
        # Heuristic: Is this folder name in the registry?
        # or is this exact path in the registry?
        
        is_tracked = False
        # Check explicit path match
        # (Skip for now, requires complex path normalization)
        
        # Check broad ID match
        if pid_guess in expected_ids:
            is_tracked = True
            
        if not is_tracked:
            rogues.append({
                "path": path_str,
                "guessed_id": pid_guess,
                "status": "untracked"
            })

    return {
        "scanner": "architecture.drift",
        "workspaces_scanned": [str(w) for w in workspaces],
        "metrics": {
            "total_expected": len(expected_projects),
            "total_found": len(actual_projects_map),
            "ghost_count": len(ghosts),
            "rogue_count": len(rogues),
            "match_count": len(matches)
        },
        "ghosts": ghosts,
        "rogues": rogues
    }
