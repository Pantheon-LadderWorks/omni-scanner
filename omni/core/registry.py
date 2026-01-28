import os
import yaml

# Configuration (Migrated from surface_scanner.py)
REGISTRY_PATH = r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.md"
PANTHEON_REGISTRY_PATH = r"C:\Users\kryst\Infrastructure\conversation-memory-project\PANTHEON_PROJECT_REGISTRY.final.yaml"
WORKSPACE_ROOT = r"C:\Users\kryst"

def parse_registry():
    projects_md = _parse_md_registry(REGISTRY_PATH)
    projects_yaml = _parse_pantheon_registry(PANTHEON_REGISTRY_PATH)
    
    projects_map = {}
    for p in projects_md + projects_yaml:
        norm_path = os.path.normpath(p['path'].lower())
        if norm_path not in projects_map:
             projects_map[norm_path] = p
    
    return list(projects_map.values())

def _parse_md_registry(registry_path):
    projects = []
    if not os.path.exists(registry_path):
        return projects

    with open(registry_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = ""
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
                
                full_path = os.path.join(WORKSPACE_ROOT, current_section.split(" ")[0] if current_section else "Infrastructure", path_raw)
                
                if "Infrastructure" in registry_path and not os.path.isabs(path_raw):
                     candidates = [
                         os.path.join(r"C:\Users\kryst\Infrastructure", path_raw),
                         os.path.join(r"C:\Users\kryst\Deployment", path_raw),
                         os.path.join(r"C:\Users\kryst\Workspace", path_raw),
                     ]
                     for c in candidates:
                         if os.path.exists(c):
                             full_path = c
                             break
                
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

def _parse_pantheon_registry(registry_path):
    projects = []
    if not os.path.exists(registry_path):
        return projects

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        for proj in data.get('projects', []):
            if proj.get('status') != 'active': continue
            local_paths = proj.get('local_paths', [])
            if not local_paths: continue
            
            # YAML doesn't have UUIDs yet, but checking if they appear
            uuid_str = proj.get('uuid')
            
            for path in local_paths:
                full_path = path
                if not os.path.isabs(full_path):
                     full_path = os.path.join(WORKSPACE_ROOT, path)

                projects.append({
                    "name": proj['display_name'],
                    "path": full_path,
                    "type": proj.get('classification', 'unknown'),
                    "uuid": uuid_str
                })
    except Exception:
        pass
        
    return projects
