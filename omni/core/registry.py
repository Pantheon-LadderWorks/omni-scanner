import os
import yaml
from pathlib import Path
from omni.config import settings

def parse_registry(include_virtual=False):
    """
    Parse canonical PROJECT_REGISTRY_V1.yaml.
    
    Args:
        include_virtual: If True, include virtual projects (no local paths).
                        Default False for backward compatibility.
    
    Returns:
        List of project dicts for consumers (like cli.py).
    """
    registry_path = settings.get_project_registry_path()
    
    if not registry_path.exists():
        return []

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        projects = []
        for p in data.get('projects', []):
            local_paths = p.get('local_paths', [])
            
            # Skip virtual projects unless explicitly included
            if not local_paths and not include_virtual:
                continue
                
            # For physical projects, extract primary path
            # For virtual projects, path is None
            primary_path = local_paths[0] if local_paths else None
            
            projects.append({
                "name": p.get('name', ''),
                "display_name": p.get('display_name', ''),
                "path": primary_path,
                "uuid": p.get('uuid'),
                "type": p.get('classification', 'unknown'),
                "github_url": p.get('github_url'),
                "status": p.get('status', 'unknown'),
                "origin": p.get('origin', 'unknown'),
                "local_paths": local_paths,
                "domain": p.get('domain'),
                "visibility": p.get('visibility')
            })
            
        return projects
        
    except Exception as e:
        print(f"❌ Failed to parse registry: {e}")
        return []

def _parse_md_registry(registry_path):
    """Legacy MD Parser (Maintained for bootstrapping builder)."""
    projects = []
    if not os.path.exists(registry_path):
        return projects

    with open(registry_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = ""
    # Assuming standard infrastructure root if settings unavailable (legacy mode)
    workspace_root = r"C:\Users\kryst" 
    
    for line in lines:
        if line.startswith("##"):
            current_section = line.strip().replace("#", "").strip()
        
        if "|" in line and "Path" in line: continue
        if "|" in line and "---" in line: continue

        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 4:
                name = parts[1].strip("**")
                path_raw = parts[3].strip("`")
                if "{" in path_raw: continue
                
                full_path = os.path.join(workspace_root, current_section.split(" ")[0] if current_section else "Infrastructure", path_raw)
                
                # Extract UUID (Col 2)
                uuid_str = parts[2].strip("` ")
                if uuid_str in ["-", ""]:
                    uuid_str = None

                projects.append({
                    "name": name,
                    "path": full_path,
                    "type": parts[4],
                    "uuid": uuid_str
                })
    return projects

def parse_master_registry_md(registry_path):
    """
    Parse master registry to extract legacy UUIDs.
    Returns dict of { 'github:owner/repo': 'uuid-string' }
    """
    legacy_map = {}
    projects = _parse_md_registry(registry_path)
    
    for p in projects:
        if p.get('uuid'):
            # Convert path to project_key format
            # This is approximate - real matching is in identity_engine
            name = p.get('name', '').lower().replace(' ', '-')
            key = f"github:kryssie6985/{name}"
            legacy_map[key] = p['uuid']
    
    return legacy_map
