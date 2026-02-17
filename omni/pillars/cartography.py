"""
omni/pillars/cartography.py
The Active Cartographer
========================
Responsibility:
1.  Project Identity Resolution (The "One Ring").
2.  Map Validation (Manifest vs. Disk).
3.  Database Sync (Fetcher).

This uses the 'Federation Heart' (via settings) to know where things SHOULD be,
and the 'Scanners' to see where things ARE.

Pattern: Librarian (Heart) tells expected state, Surveyor (Pillar) measures actual state.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# 1. The Logic (The Brains) - from core
from omni.core.identity_engine import (
    ProjectIdentity, 
    RepoInventoryItem, 
    IdentityScanResult,
    IdentityPatch,
    NAMESPACE_CMP
)

logger = logging.getLogger("Omni.Pillar.Cartography")


class CartographyPillar:
    """
    The Active Cartographer.
    
    Uses Heart (settings) for expected state.
    Uses Scanners for actual state.
    Uses identity_engine for reconciliation.
    """
    
    def __init__(self, settings_module):
        self.settings = settings_module
        self.heart_available = self.settings.heart_available()
        
        # Access Heart Clients via shim (if available)
        self.heart_cartography = self.settings.cartography
        self.heart_constitution = self.settings.constitution
        
        logger.info("🗺️ Cartography Pillar initialized")
        logger.info(f"   - Heart Available: {self.heart_available}")
    
    # =========================================================================
    # Path Resolution (Delegates to Heart or Fallback)
    # =========================================================================
    
    def get_infrastructure_root(self) -> Path:
        """Pass-through to Heart, or fallback."""
        return self.settings.get_infrastructure_root()
    
    def get_governance_path(self, relative: str = "") -> Path:
        """Get governance path with optional relative suffix."""
        return self.settings.get_governance_path(relative)
    
    def get_artifacts_path(self) -> Path:
        """Get artifacts output path."""
        return self.settings.get_artifacts_path()
    
    # =========================================================================
    # Identity Reconciliation (The Master Operation)
    # =========================================================================
    
    def scan_ecosystem_identity(
        self, 
        inventory_path: Optional[Path] = None
    ) -> IdentityScanResult:
        """
        The Master Audit.
        Reconciles GitHub Inventory vs. CMP Database vs. Local Paths.
        
        Args:
            inventory_path: Path to repo_inventory.json (defaults to governance registry)
            
        Returns:
            IdentityScanResult with all resolved project identities
        """
        logger.info("🗺️ Starting Ecosystem Identity Scan...")
        
        # 1. Resolve inventory path
        if inventory_path is None:
            inventory_path = self.get_governance_path("registry/git_repos/repo_inventory.json")
        
        if not inventory_path.exists():
            logger.error(f"❌ Inventory not found: {inventory_path}")
            raise FileNotFoundError(f"Inventory not found: {inventory_path}")
        
        # 2. Load Inventory (Raw Input)
        logger.info(f"   Loading inventory: {inventory_path}")
        with open(inventory_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            # Handle list vs dict wrapper
            items = raw_data if isinstance(raw_data, list) else raw_data.get("projects", [])
        
        # Deduplicate by URL
        seen_urls = set()
        unique_items = []
        for item in items:
            url = item.get('url', '').lower()
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_items.append(item)
        
        inventory = [RepoInventoryItem(**item) for item in unique_items]
        logger.info(f"   Loaded {len(inventory)} unique repositories")
        
        # 3. Load CMP Database State (The Knowledge)
        known_identities = self._fetch_known_identities()
        
        # 4. Load Master Registry Oracle (The History)
        legacy_oracle = self._load_legacy_oracle()
        
        # 5. Load CMP Project Data (for enrichment)
        cmp_data = self._load_cmp_registry()
        
        # 6. Resolve Each Project (The Engine)
        projects: List[ProjectIdentity] = []
        stats = {"total": 0, "new": 0, "conflict": 0, "converged": 0, "keyed": 0}
        
        for item in inventory:
            identity = ProjectIdentity.resolve(
                item,
                existing_db_map=known_identities,
                legacy_oracle=legacy_oracle,
                cmp_data=cmp_data
            )
            projects.append(identity)
            
            # Update Stats
            stats["total"] += 1
            if identity.identity_status == "discovered":
                stats["new"] += 1
            elif identity.identity_status == "conflict":
                stats["conflict"] += 1
            elif identity.identity_status == "keyed":
                stats["keyed"] += 1
            else:
                stats["converged"] += 1
        
        logger.info(f"   ✅ Resolved {stats['total']} identities")
        logger.info(f"      - Converged: {stats['converged']}")
        logger.info(f"      - Keyed: {stats['keyed']}")
        logger.info(f"      - New: {stats['new']}")
        logger.info(f"      - Conflicts: {stats['conflict']}")
        
        # 7. Return Result
        return IdentityScanResult(
            generated_at=datetime.now(timezone.utc).isoformat(),
            namespace_used=str(NAMESPACE_CMP),
            stats=stats,
            projects=projects
        )
    
    def generate_identity_patch(
        self, 
        scan_result: IdentityScanResult
    ) -> IdentityPatch:
        """
        Generate patch actions from scan result.
        
        Returns:
            IdentityPatch with actions to apply
        """
        actions = []
        
        for project in scan_result.projects:
            # CMP_CREATE for new projects not in CMP
            if project.cmp_status == "missing":
                actions.append({
                    "action": "CMP_CREATE",
                    "project_key": project.project_key,
                    "project_uuid": project.project_uuid,
                    "display_name": project.display_name,
                    "github_url": project.github_url,
                    "reason": f"Not found in CMP (status: {project.identity_status})"
                })
            
            # CMP_BACKFILL_UUID for projects in CMP without UUID
            elif project.cmp_status == "found_no_uuid":
                actions.append({
                    "action": "CMP_BACKFILL_UUID",
                    "project_key": project.project_key,
                    "project_uuid": project.project_uuid,
                    "reason": "CMP entry exists but missing UUID"
                })
        
        return IdentityPatch(
            generated_at=datetime.now(timezone.utc).isoformat(),
            source_scan=scan_result.generated_at,
            actions=actions,
            stats={
                "total_actions": len(actions),
                "creates": sum(1 for a in actions if a["action"] == "CMP_CREATE"),
                "backfills": sum(1 for a in actions if a["action"] == "CMP_BACKFILL_UUID"),
            }
        )
    
    # =========================================================================
    # Station/Registry Auditing
    # =========================================================================
    
    def audit_station_registry(self) -> List[str]:
        """
        Check if registered stations actually exist on disk.
        
        Returns:
            List of audit messages (errors or success)
        """
        if not self.heart_available:
            return ["⚠️ Heart unavailable - cannot audit registry."]
        
        errors = []
        
        try:
            stations = self.heart_cartography.list_stations()
        except Exception as e:
            return [f"❌ Failed to list stations: {e}"]
        
        for station in stations:
            sid = station.get('id', 'unknown')
            try:
                # Check if station folder exists
                stations_root = self.get_infrastructure_root() / "stations"
                station_path = stations_root / sid.replace("station_", "").replace("_station", "_station")
                
                if not station_path.exists():
                    errors.append(f"❌ Station '{sid}' registered but folder missing")
            except Exception as e:
                errors.append(f"❌ Station '{sid}' path resolution failed: {e}")
        
        return errors if errors else ["✅ All stations accounted for."]
    
    # =========================================================================
    # Private Helpers
    # =========================================================================
    
    def _fetch_known_identities(self) -> Dict[str, str]:
        """
        Connects to CMS DB (if available) to get current UUID map.
        
        Returns:
            Dict mapping project_key -> uuid
        """
        # For now, return empty - Phase B will implement actual DB call
        # via fetcher.py or direct SQL
        return {}
    
    def _load_legacy_oracle(self) -> Dict[str, str]:
        """
        Loads the Master Registry MD/YAML to preserve legacy UUIDs.
        
        Returns:
            Dict mapping project_key -> legacy_uuid
        """
        oracle = {}
        master_path = self.get_governance_path("registry/projects/PROJECT_REGISTRY_MASTER.md")
        
        if master_path.exists():
            try:
                from omni.core.registry import parse_master_registry_md
                oracle = parse_master_registry_md(master_path)
                logger.info(f"   Loaded {len(oracle)} legacy UUIDs from master registry")
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to load legacy oracle: {e}")
        
        return oracle
    
    def _load_cmp_registry(self) -> Dict[str, Any]:
        """
        Load CMP project registry for enrichment.
        
        Returns:
            Dict mapping project_name -> cmp_data
        """
        cmp_data = {}
        cmp_path = self.settings.get_cmp_registry_path()
        
        if cmp_path and cmp_path.exists():
            try:
                import yaml
                with open(cmp_path, 'r', encoding='utf-8') as f:
                    registry = yaml.safe_load(f)
                
                for project in registry.get("projects", []):
                    name = project.get("name", "").lower()
                    if name:
                        cmp_data[name] = project
                
                logger.info(f"   Loaded {len(cmp_data)} projects from CMP registry")
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to load CMP registry: {e}")
        
        return cmp_data
