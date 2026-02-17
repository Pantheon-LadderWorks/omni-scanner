"""
omni/core/canonical_uuid_builder.py
Canonical UUID Registry Builder
================================
Generates canonical_projects_uuids.json and canonical_agents_uuids.json
from authoritative sources (CMP database, file registry, GitHub inventory).

Replaces the monolithic canonical_uuids.json with separate entity-type files.

Sources:
1. CMP Database (via database scanners) - PRIMARY for projects/agents
2. File-based registries (COUNCIL_UUID_REGISTRY.yaml, PROJECT_REGISTRY_V1.yaml)
3. GitHub inventory (repo_inventory.json)

Output:
- canonical_projects_uuids.json - All project UUIDs with metadata
- canonical_agents_uuids.json - All agent UUIDs with metadata

Uses federation_heart for path resolution (CartographyPillar).
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Import federation_heart pillars (pip installed as seraphina-federation)
try:
    from federation_heart.pillars.cartography import CartographyPillar
    from federation_heart.pillars.constitution import ConstitutionPillar
    HEART_AVAILABLE = True
except ImportError as e:
    HEART_AVAILABLE = False
    _import_error = str(e)

logger = logging.getLogger("Omni.Core.CanonicalUUIDBuilder")


@dataclass
class CanonicalUUID:
    """A canonical UUID entry."""
    uuid: str
    name: str
    type: str  # PROJECT, AGENT, STATION, etc.
    key: Optional[str] = None
    github_url: Optional[str] = None
    domain: Optional[str] = None
    role: Optional[str] = None
    status: str = "active"
    source: str = "unknown"  # cmp_db, file_registry, github_inventory
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, omitting None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CanonicalUUIDRegistry:
    """A canonical UUID registry (projects or agents)."""
    version: str
    entity_type: str  # "projects" or "agents"
    generated_at: str
    count: int
    uuids: Dict[str, Dict[str, Any]]  # {uuid: metadata}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "entity_type": self.entity_type,
            "generated_at": self.generated_at,
            "count": self.count,
            "uuids": self.uuids
        }


class CanonicalUUIDBuilder:
    """
    Builds canonical UUID registries from database and file sources.
    Uses federation_heart for path resolution.
    """
    
    def __init__(self, infra_root: Path = None):
        if not HEART_AVAILABLE:
            raise RuntimeError(f"Federation Heart not available: {_import_error}")
        
        # Initialize pillars
        self._cartography = CartographyPillar(infra_root)
        self._constitution = ConstitutionPillar(self._cartography.root, self._cartography)
        
        self.infra_root = self._cartography.get_infrastructure_root()
        
        logger.info(f"🔧 CanonicalUUIDBuilder initialized")
        logger.info(f"   - Infrastructure: {self.infra_root}")
    
    def build_projects(self) -> CanonicalUUIDRegistry:
        """
        Build canonical projects UUID registry.
        
        CMP Database is the SINGLE SOURCE OF TRUTH.
        File registry is drifted and must be OVERWRITTEN, not consulted.
        This generates what the registry SHOULD be.
        """
        logger.info("🏗️ Building canonical projects UUIDs...")
        logger.info("   📡 CMP Database is SINGLE SOURCE OF TRUTH")
        
        uuids = {}
        
        # Load from CMP Database (ONLY source)
        cmp_projects = self._load_cmp_projects()
        logger.info(f"   ✅ Loaded {len(cmp_projects)} projects from CMP database")
        
        for proj in cmp_projects:
            uuid = str(proj['uuid'])  # Convert UUID to string for JSON serialization
            uuids[uuid] = {
                'name': proj['name'],
                'type': proj.get('type', 'PROJECT'),
                'key': proj.get('key'),
                'github_url': proj.get('github_url'),
                'domain': proj.get('domain'),
                'status': proj.get('status', 'active'),
                'source': 'cmp_db'
            }
        
        logger.info(f"   ✅ Built {len(uuids)} canonical project UUIDs")
        
        return CanonicalUUIDRegistry(
            version="1.0.0",
            entity_type="projects",
            generated_at=datetime.now(timezone.utc).isoformat(),
            count=len(uuids),
            uuids=uuids
        )
    
    def build_agents(self) -> CanonicalUUIDRegistry:
        """
        Build canonical agents UUID registry.
        
        CMP Database is the SINGLE SOURCE OF TRUTH.
        File registry is drifted and must be OVERWRITTEN, not consulted.
        This generates what the registry SHOULD be.
        """
        logger.info("🏗️ Building canonical agents UUIDs...")
        logger.info("   📡 CMP Database is SINGLE SOURCE OF TRUTH")
        
        uuids = {}
        
        # Load from CMP Database (ONLY source)
        cmp_agents = self._load_cmp_agents()
        logger.info(f"   ✅ Loaded {len(cmp_agents)} agents from CMP database")
        
        for agent in cmp_agents:
            uuid = str(agent['uuid'])  # Convert UUID to string for JSON serialization
            uuids[uuid] = {
                'name': agent['name'],
                'type': 'AGENT',
                'kind': agent.get('kind'),
                'role': agent.get('role'),
                'clearance_tier': agent.get('clearance_tier'),
                'twin_bond': agent.get('twin_bond'),
                'status': 'active',
                'source': 'cmp_db'
            }
        
        logger.info(f"   ✅ Built {len(uuids)} canonical agent UUIDs")
        
        return CanonicalUUIDRegistry(
            version="1.0.0",
            entity_type="agents",
            generated_at=datetime.now(timezone.utc).isoformat(),
            count=len(uuids),
            uuids=uuids
        )
    
    def save(
        self,
        registry: CanonicalUUIDRegistry,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Save canonical UUID registry to JSON file.
        
        Args:
            registry: The built registry
            output_dir: Output directory (defaults to governance/registry/uuid/)
        
        Returns:
            Path to saved file
        """
        if output_dir is None:
            # Use CartographyPillar to resolve governance path
            governance_root = self._cartography.resolve_path("governance")
            output_dir = governance_root / "registry" / "uuid"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"canonical_{registry.entity_type}_uuids.json"
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(registry.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"   💾 Saved to: {output_path}")
        logger.info(f"      {registry.count} {registry.entity_type} UUIDs")
        
        return output_path
    
    # =========================================================================
    # Data Loaders (using scanners)
    # =========================================================================
    
    def _load_cmp_projects(self) -> List[Dict[str, Any]]:
        """Load projects from CMP database via scanner."""
        try:
            from omni.scanners.database.cmp_projects import scan
            result = scan(self.infra_root)
            return result.get('items', [])
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load CMP projects: {e}")
            return []
    
    def _load_cmp_agents(self) -> List[Dict[str, Any]]:
        """Load agents from CMP database via scanner."""
        try:
            from omni.scanners.database.cmp_agents import scan
            result = scan(self.infra_root)
            return result.get('items', [])
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load CMP agents: {e}")
            return []
    
    def _load_project_registry(self) -> List[Dict[str, Any]]:
        """Load PROJECT_REGISTRY_V1.yaml via CartographyPillar."""
        try:
            import yaml
            # Use CartographyPillar to resolve path
            governance_root = self._cartography.resolve_path("governance")
            registry_path = governance_root / "registry" / "projects" / "PROJECT_REGISTRY_V1.yaml"
            
            if not registry_path or not registry_path.exists():
                return []
            
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            return data.get('projects', [])
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load PROJECT_REGISTRY: {e}")
            return []
    
    def _load_council_registry(self) -> List[Dict[str, Any]]:
        """Load COUNCIL_UUID_REGISTRY.yaml via CartographyPillar."""
        try:
            import yaml
            # Use CartographyPillar to resolve path
            agents_root = self._cartography.resolve_path("agents")
            registry_path = agents_root / "COUNCIL_UUID_REGISTRY.yaml"
            
            if not registry_path or not registry_path.exists():
                return []
            
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Extract agents with UUIDs
            agents = []
            for agent_data in data.get('agents', []):
                if agent_data.get('cmp_agent_id'):
                    agents.append({
                        'uuid': agent_data['cmp_agent_id'],
                        'name': agent_data.get('name'),
                        'role': agent_data.get('role'),
                        'clearance_tier': agent_data.get('clearance_tier'),
                        'status': 'active'
                    })
            
            return agents
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load COUNCIL_UUID_REGISTRY: {e}")
            return []


def build_canonical_uuids(
    output_dir: Optional[Path] = None,
    projects: bool = True,
    agents: bool = True
) -> Dict[str, Path]:
    """
    Convenience function to build and save canonical UUID registries.
    
    Args:
        output_dir: Output directory for JSON files
        projects: Whether to build projects registry
        agents: Whether to build agents registry
    
    Returns:
        Dict of {entity_type: saved_path}
    """
    builder = CanonicalUUIDBuilder()
    saved = {}
    
    if projects:
        registry = builder.build_projects()
        saved['projects'] = builder.save(registry, output_dir)
    
    if agents:
        registry = builder.build_agents()
        saved['agents'] = builder.save(registry, output_dir)
    
    return saved


if __name__ == "__main__":
    # Standalone test
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Canonical UUID Registry Builder Test")
    print("="*60 + "\n")
    
    saved = build_canonical_uuids()
    
    print("\n✅ Build Complete!")
    for entity_type, path in saved.items():
        print(f"   {entity_type}: {path}")
