import yaml
import re
from pathlib import Path

REGISTRY_PATH = Path(r"C:\Users\kryst\Infrastructure\PROJECT_REGISTRY_MASTER.md")

def load_v2_registry(path=REGISTRY_PATH):
    """
    Parses the Schema V2 Registry (Frontmatter-based).
    Returns a unified list of 'scannable items' (UUID-bearing entities).
    """
    if not path.exists():
        return {"error": f"Registry not found: {path}"}
        
    content = path.read_text(encoding='utf-8')
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {"error": "No frontmatter found in registry"}
        
    try:
        data = yaml.safe_load(match.group(1))
    except Exception as e:
        return {"error": f"YAML parse error: {e}"}
        
    return parse_v2_data(data)

def parse_v2_data(data):
    """
    Flattens the V2 structure into a simple 'canonical map' for tools.
    """
    canon_map = {}
    
    # 1. Process Entities (Identity + Facets)
    for ent in data.get('entities', []):
        c_id = ent['canonical_id']
        name = ent['display_name']
        
        # Base entry
        canon_map[c_id] = {
            "type": "ENTITY",
            "kind": ent.get('kind', 'entity'),
            "name": name,
            "role": ent.get('role'),
            "source": "REGISTRY_V2:frontmatter"
        }
        
        # Facets providing UUIDs
        if 'facets' in ent:
            # Agent Persona UUID
            if 'agent_persona' in ent['facets']:
                uuid = ent['facets']['agent_persona'].get('id')
                if uuid:
                     canon_map[uuid.lower()] = {
                         "type": "FACET_AGENT",
                         "canonical_id": c_id,
                         "name": f"{name} (Agent)",
                         "source": "REGISTRY_V2:facet"
                     }
            
            # Core UUID (for stations/tools/misc)
            if 'core' in ent['facets']:
                uuid = ent['facets']['core'].get('id')
                if uuid:
                     canon_map[uuid.lower()] = {
                         "type": "FACET_CORE",
                         "canonical_id": c_id,
                         "name": f"{name} (Core)",
                         "source": "REGISTRY_V2:facet"
                     }

            # Station Core
            if 'station_core' in ent['facets']:
                 uuid = ent['facets']['station_core'].get('id')
                 if uuid:
                      canon_map[uuid.lower()] = {
                          "type": "FACET_STATION",
                          "canonical_id": c_id,
                          "name": f"{name} (Station)",
                          "source": "REGISTRY_V2:facet"
                      }

    # 2. Process Standalone Projects (that might have UUIDs)
    for proj in data.get('projects', []):
        # Check if project has a UUID (some might in 'ids' dict if we expanded schema, 
        # but current `refactor` script didn't populate UUIDs for projects unless they were entities)
        # However, `PROJECT_REGISTRY_MASTER.yaml` had `id` field.
        # Let's see if we preserved it.
        # The refactor script puts them in `projects` list but schema V2 `projects` table 
        # usually is just repo pointers.
        # If a project has a UUID, it SHOULD be an Entity in V2 logic.
        pass

    return canon_map
