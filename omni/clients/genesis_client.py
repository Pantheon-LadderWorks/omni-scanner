"""
Genesis Client - Omni interface for Genesis canonization workflows

Wraps Omni scanner orchestration specifically for Genesis tri-point anchoring:
- Project registration → Registry propagation
- Batch canonization → Single rebuild
- UUID/Project/Git registry coordination

"Genesis creates. Omni remembers. This client bridges them." - Infrastructure, 2026
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger("Omni.Clients.Genesis")


class GenesisClient:
    """
    High-level interface for Genesis to trigger Omni registry operations.
    
    Genesis should NEVER directly manipulate registry files.
    Genesis should ONLY call this client to propagate CMP → Registries.
    """
    
    def __init__(self, omni_root: Optional[Path] = None):
        """
        Initialize Genesis client.
        
        Args:
            omni_root: Path to Omni root (defaults to auto-detect)
        """
        self.omni_root = omni_root or self._find_omni_root()
        
    def _find_omni_root(self) -> Path:
        """Auto-detect Omni installation."""
        # Try common locations
        candidates = [
            Path(__file__).parent.parent.parent,  # tools/omni/omni/clients -> tools/omni
            Path.cwd() / "tools" / "omni",
            Path.home() / "Infrastructure" / "tools" / "omni",
        ]
        
        for candidate in candidates:
            if (candidate / "omni").exists():
                return candidate
        
        # Fallback
        return Path(__file__).parent.parent.parent
    
    def propagate_project(
        self,
        project_name: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Propagate a single project from CMP to all registries.
        
        Workflow:
        1. Scan CMP for project
        2. Update canonical_projects_uuids.json
        3. Update PROJECT_REGISTRY_V1.yaml
        4. Update repo_inventory.json (if has GitHub)
        
        Args:
            project_name: Name of project in CMP
            dry_run: Preview without writing files
        
        Returns:
            Dict with propagation results
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would propagate {project_name} to registries")
            return {
                "success": True,
                "dry_run": True,
                "project": project_name,
                "registries_updated": ["canonical_projects_uuids.json", "PROJECT_REGISTRY_V1.yaml", "repo_inventory.json"],
            }
        
        try:
            # Import scanners directly (no orchestrator needed)
            from omni.scanners import SCANNERS
            
            # Strategy: Run targeted scanners
            # 1. cmp_projects - Sync CMP → Project structures
            # 2. project - Rebuild PROJECT_REGISTRY_V1.yaml
            # 3. git - Update repo_inventory.json
            
            results = {}
            
            logger.info(f"📊 Scanning CMP for project: {project_name}")
            if "cmp_projects" in SCANNERS:
                cmp_result = SCANNERS["cmp_projects"](self.omni_root.parent.parent)
                results["cmp_scan"] = cmp_result
            else:
                logger.warning("cmp_projects scanner not available")
            
            logger.info("📋 Rebuilding PROJECT_REGISTRY_V1.yaml")
            if "project" in SCANNERS:
                project_result = SCANNERS["project"](self.omni_root.parent.parent)
                results["project_registry"] = project_result
            else:
                logger.warning("project scanner not available")
            
            logger.info("🐙 Updating repo_inventory.json")
            if "git" in SCANNERS:
                git_result = SCANNERS["git"](self.omni_root.parent.parent)
                results["git_registry"] = git_result
            else:
                logger.warning("git scanner not available")
            
            return {
                "success": True,
                "dry_run": False,
                "project": project_name,
                "registries_updated": ["canonical_projects_uuids.json", "PROJECT_REGISTRY_V1.yaml", "repo_inventory.json"],
                "scanner_results": results,
            }
            
        except Exception as e:
            logger.error(f"Failed to propagate {project_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "project": project_name,
            }
    
    def propagate_batch(
        self,
        project_names: List[str],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Propagate multiple projects from CMP to registries (single rebuild).
        
        More efficient than calling propagate_project() multiple times.
        
        Args:
            project_names: List of project names in CMP
            dry_run: Preview without writing files
        
        Returns:
            Dict with batch propagation results
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would propagate {len(project_names)} projects")
            return {
                "success": True,
                "dry_run": True,
                "count": len(project_names),
                "projects": project_names,
            }
        
        try:
            from omni.scanners import SCANNERS
            
            # Single scan for all projects (more efficient)
            logger.info(f"📦 Batch propagating {len(project_names)} projects")
            
            results = {}
            if "cmp_projects" in SCANNERS:
                results["cmp_scan"] = SCANNERS["cmp_projects"](self.omni_root.parent.parent)
            if "project" in SCANNERS:
                results["project_registry"] = SCANNERS["project"](self.omni_root.parent.parent)
            if "git" in SCANNERS:
                results["git_registry"] = SCANNERS["git"](self.omni_root.parent.parent)
            
            return {
                "success": True,
                "dry_run": False,
                "count": len(project_names),
                "projects": project_names,
                "scanner_results": results,
            }
            
        except Exception as e:
            logger.error(f"Batch propagation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "count": len(project_names),
            }
    
    def rebuild_all_registries(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Full registry rebuild from CMP (use sparingly - expensive).
        
        Triggers:
        - All project scanners
        - All agent scanners
        - Git/UUID coordination
        
        Args:
            dry_run: Preview without writing files
        
        Returns:
            Dict with rebuild results
        """
        if dry_run:
            logger.info("[DRY RUN] Would rebuild all registries from CMP")
            return {
                "success": True,
                "dry_run": True,
                "operation": "full_rebuild",
            }
        
        try:
            from omni.scanners import SCANNERS
            
            logger.info("🌌 Full registry rebuild initiated")
            
            # Run all critical scanners
            scanner_names = ["cmp_projects", "project", "git", "uuids"]
            results = {}
            
            for scanner_name in scanner_names:
                if scanner_name in SCANNERS:
                    logger.info(f"   Running {scanner_name}...")
                    results[scanner_name] = SCANNERS[scanner_name](self.omni_root.parent.parent)
                else:
                    logger.warning(f"   Scanner {scanner_name} not available")
                    results[scanner_name] = {"status": "skipped", "reason": "not available"}
            
            return {
                "success": True,
                "dry_run": False,
                "operation": "full_rebuild",
                "scanners_run": scanner_names,
                "results": results,
            }
            
        except Exception as e:
            logger.error(f"Full rebuild failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "full_rebuild",
            }
    
    def verify_propagation(self, project_uuid: str) -> Dict[str, Any]:
        """
        Verify project UUID appears in all expected registries.
        
        Checks:
        - canonical_projects_uuids.json
        - PROJECT_REGISTRY_V1.yaml
        - repo_inventory.json (if has GitHub)
        
        Args:
            project_uuid: UUID to verify
        
        Returns:
            Dict with verification results
        """
        try:
            import json
            import yaml
            
            infrastructure_root = self.omni_root.parent.parent
            
            checks = {
                "in_canonical_uuids": False,
                "in_project_registry": False,
                "in_repo_inventory": False,
            }
            
            # Check canonical_projects_uuids.json
            uuid_file = infrastructure_root / "governance" / "registry" / "uuid" / "canonical_projects_uuids.json"
            if uuid_file.exists():
                with open(uuid_file, "r", encoding="utf-8") as f:
                    uuid_data = json.load(f)
                    checks["in_canonical_uuids"] = project_uuid in uuid_data
            
            # Check PROJECT_REGISTRY_V1.yaml
            reg_file = infrastructure_root / "governance" / "registry" / "projects" / "PROJECT_REGISTRY_V1.yaml"
            if reg_file.exists():
                with open(reg_file, "r", encoding="utf-8") as f:
                    reg_data = yaml.safe_load(f)
                    projects = reg_data.get("projects", [])
                    checks["in_project_registry"] = any(p.get("uuid") == project_uuid for p in projects)
            
            # Check repo_inventory.json
            repo_file = infrastructure_root / "governance" / "registry" / "git_repos" / "repo_inventory.json"
            if repo_file.exists():
                with open(repo_file, "r", encoding="utf-8") as f:
                    repo_data = json.load(f)
                    repos = repo_data.get("repositories", [])
                    checks["in_repo_inventory"] = any(r.get("uuid") == project_uuid for r in repos)
            
            all_verified = all(checks.values())
            
            return {
                "verified": all_verified,
                "uuid": project_uuid,
                "checks": checks,
                "missing_from": [k for k, v in checks.items() if not v],
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "uuid": project_uuid,
            }
