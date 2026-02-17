"""
omni/core/registry_builder.py
The Registry Builder
====================
Derives PROJECT_REGISTRY_V1.yaml from authoritative sources.

This is CORE logic - it computes the truth.
The scanner wrapper (scanners/discovery/project.py) will call this.

Sources:
1. GitHub Inventory (repo_inventory.json) - what exists in cloud
2. CMP Registry (WIP) - what's registered in database
3. Local Filesystem - what exists on disk
4. Identity Engine - resolves UUIDs

Output:
- PROJECT_REGISTRY_V1.yaml - canonical project registry
"""
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict

from omni.core.identity_engine import (
    ProjectIdentity,
    RepoInventoryItem,
    IdentityScanResult,
    NAMESPACE_CMP
)

logger = logging.getLogger("Omni.Core.RegistryBuilder")


@dataclass
class RegistryProject:
    """A project entry in the registry."""
    uuid: str
    name: str
    display_name: str
    github_url: Optional[str]
    local_paths: List[str]
    classification: str
    status: str
    origin: str
    
    # Metadata
    visibility: str = "private"
    updated_at: Optional[str] = None
    notes: Optional[str] = None
    
    # Heart integration
    heart_connected: bool = False
    heart_import_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectRegistry:
    """The complete project registry."""
    version: str
    generated_at: str
    namespace: str
    stats: Dict[str, int]
    projects: List[RegistryProject]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "namespace": self.namespace,
            "stats": self.stats,
            "projects": [p.to_dict() for p in self.projects]
        }


class RegistryBuilder:
    """
    Builds PROJECT_REGISTRY_V1.yaml from authoritative sources.
    """
    
    def __init__(self, settings_module=None):
        if settings_module is None:
            from omni.config import settings
            self.settings = settings
        else:
            self.settings = settings_module
        
        self.infra_root = self.settings.get_infrastructure_root()
        logger.info(f"📦 RegistryBuilder initialized")
        logger.info(f"   - Infrastructure: {self.infra_root}")
    
    def build(
        self,
        inventory_path: Optional[Path] = None,
        include_local_only: bool = True,
        scan_local: bool = True
    ) -> ProjectRegistry:
        """
        Build the project registry from CMP database (CROWN TRUTH).
        
        CMP is the DRIVER. GitHub and local paths are ENRICHMENT.
        
        Args:
            inventory_path: Path to repo_inventory.json (for enrichment)
            include_local_only: Whether to include local-only projects
            scan_local: Whether to scan filesystem for local paths
            
        Returns:
            ProjectRegistry mirroring CMP database
        """
        logger.info("🔨 Building Project Registry...")
        logger.info("   📡 CMP Database is SINGLE SOURCE OF TRUTH")
        
        # 0. Load Local Overrides (Tier 0 Truth)
        overrides_map = self._load_overrides()
        logger.info(f"   Loaded {len(overrides_map)} local overrides")

        # 1. Load CMP Database (THE DRIVER)
        cmp_projects = self._load_cmp_data()
        logger.info(f"   ✅ Loaded {len(cmp_projects)} projects from CMP database")
        
        # 2. Load GitHub inventory as LOOKUP map
        if inventory_path is None:
            inventory_path = self.settings.get_governance_path(
                "registry/git_repos/repo_inventory.json"
            )
        
        github_map = self._load_github_inventory_as_map(inventory_path)
        logger.info(f"   Loaded {len(github_map)} GitHub repos (enrichment)")
        
        # 3. Load exclusions
        exclusions = self._load_exclusions()
        logger.info(f"   Loaded {len(exclusions)} exclusions")
        
        # 4. Scan local filesystem for git repos (maps URL -> local path)
        local_path_map = {}
        if scan_local:
            logger.info("   🔍 Scanning local filesystem for git repos...")
            local_path_map = self._scan_local_paths()
            logger.info(f"   Found {len(local_path_map)} local git repos")
        
        # 5. Scan heart integration (which local paths have federation_heart imports?)
        heart_integration_map = self._scan_heart_integration()
        logger.info(f"   💓 Heart integration: {len(heart_integration_map)} projects connected")
        
        # 6. Iterate through CMP projects (MASTER LOOP)
        registry_projects = []
        stats = {
            "total": 0, "github": 0, "local_only": 0, 
            "linked": 0, "cloud_only": 0, "local_snapshot": 0, "virtual": 0,
            "heart_connected": 0, "heart_disconnected": 0
        }
        
        for cmp_proj in cmp_projects:
            # Extract from CMP
            uuid = str(cmp_proj['uuid'])  # Convert UUID to string for YAML serialization
            name = cmp_proj['name']
            key = cmp_proj.get('key', name)
            github_url = cmp_proj.get('github_url')
            domain = cmp_proj.get('domain')
            proj_type = cmp_proj.get('type', 'PROJECT')
            
            # Check exclusions
            if github_url and self._is_excluded(github_url, exclusions):
                logger.debug(f"   Skipping excluded: {name}")
                continue
            
            local_paths = []
            notes = None
            status = cmp_proj.get('status', 'active')
            visibility = "private"
            updated_at = None
            
            # A. Check Overrides (Highest Priority)
            if github_url:
                normalized_url = github_url.lower().rstrip('/')
                
                if normalized_url in overrides_map:
                    override = overrides_map[normalized_url]
                    if override.get('local_paths'):
                        local_paths = override['local_paths']
                    if override.get('notes'):
                        notes = override['notes']
                    if override.get('status'):
                        status = override['status']
            
            # B. GitHub Enrichment (lookup repo metadata)
            if github_url:
                normalized_url = github_url.lower().rstrip('/')
                
                if normalized_url in github_map:
                    github_repo = github_map[normalized_url]
                    visibility = github_repo.get('visibility', 'private')
                    updated_at = github_repo.get('updatedAt')
                
                # C. Local Path Enrichment (if not already from override)
                if not local_paths and normalized_url in local_path_map:
                    local_paths = [local_path_map[normalized_url]]
            
            # Heart integration check
            heart_connected = False
            heart_count = 0
            for lp in local_paths:
                # Relativize absolute paths to match heart_integration_map keys
                try:
                    lp_rel = str(
                        Path(lp).relative_to(self.infra_root)
                    ).replace("\\", "/").lower()
                except ValueError:
                    lp_rel = lp.replace("\\", "/").lower()
                
                if lp_rel in heart_integration_map:
                    heart_connected = True
                    heart_count = heart_integration_map[lp_rel]
                    break
            
            # Build registry entry
            project = RegistryProject(
                uuid=uuid,
                name=key,  # Use CMP key as canonical name
                display_name=name,  # Use CMP name as display
                github_url=github_url,
                local_paths=local_paths,
                classification=proj_type.lower(),
                status=status,
                origin="cmp_db",  # ALL entries come from CMP now
                visibility=visibility,
                updated_at=updated_at,
                notes=notes,
                heart_connected=heart_connected,
                heart_import_count=heart_count
            )
            
            registry_projects.append(project)
            stats["total"] += 1
            
            # Classification
            if github_url:
                stats["github"] += 1
            else:
                stats["virtual"] += 1
            
            if status == "snapshot":
                stats["local_snapshot"] += 1
            elif local_paths:
                stats["linked"] += 1
            elif github_url:
                stats["cloud_only"] += 1
            
            if heart_connected:
                stats["heart_connected"] += 1
            elif local_paths:  # Only count disconnected if they have local paths
                stats["heart_disconnected"] += 1
        
        # 5. Optionally scan for local-only projects
        if include_local_only:
            local_only = self._find_local_only_projects(
                {p.github_url for p in registry_projects if p.github_url}
            )
            for local in local_only:
                registry_projects.append(local)
                stats["total"] += 1
                stats["local_only"] += 1

        logger.info(f"   ✅ Registry built: {stats['total']} projects")
        logger.info(f"      Linked: {stats['linked']} | Snapshot: {stats['local_snapshot']} | Cloud Only: {stats['cloud_only']}")
        logger.info(f"      💓 Heart: {stats['heart_connected']} connected | {stats['heart_disconnected']} disconnected")
        
        return ProjectRegistry(
            version="1.0.0",
            generated_at=datetime.now(timezone.utc).isoformat(),
            namespace=str(NAMESPACE_CMP),
            stats=stats,
            projects=registry_projects
        )
    
    def save(
        self,
        registry: ProjectRegistry,
        output_path: Optional[Path] = None,
        force: bool = False
    ) -> Path:
        """
        Save the registry to YAML file.
        
        GUARD: Refuses to overwrite with worse data unless force=True.
        
        Args:
            registry: The built registry
            output_path: Where to save (defaults to governance/registry/projects/)
            force: If True, overwrite even if new data is worse
            
        Returns:
            Path to saved file
        """
        import yaml
        
        if output_path is None:
            output_path = self.settings.get_governance_path(
                "registry/projects/PROJECT_REGISTRY_V1.yaml"
            )
        
        # DEGRADATION GUARD: Don't nuke good data with empty data
        if output_path.exists() and not force:
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing = yaml.safe_load(f)
                
                old_linked = existing.get('stats', {}).get('linked', 0)
                old_github = existing.get('stats', {}).get('github', 0)
                new_linked = registry.stats.get('linked', 0)
                new_github = registry.stats.get('github', 0)
                
                # If new registry has significantly fewer linked projects, REFUSE
                if old_linked > 0 and new_linked == 0:
                    logger.error(
                        f"   🚫 SAVE BLOCKED: New registry has 0 linked projects "
                        f"but existing has {old_linked}. This looks like data loss. "
                        f"Use force=True to override."
                    )
                    raise ValueError(
                        f"Degradation guard: old={old_linked} linked, new={new_linked} linked. "
                        f"Pass force=True to overwrite."
                    )
                
                if old_github > 5 and new_github < old_github * 0.5:
                    logger.warning(
                        f"   ⚠️ New registry has {new_github} github projects "
                        f"vs existing {old_github}. Possible data loss."
                    )
            except (yaml.YAMLError, TypeError, KeyError):
                pass  # Existing file is corrupt, safe to overwrite
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                registry.to_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        
        logger.info(f"   💾 Saved to: {output_path}")
        return output_path
    
    # =========================================================================
    # Private Helpers
    # =========================================================================
    
    def _load_github_inventory(self, path: Path) -> List[RepoInventoryItem]:
        """Load and deduplicate GitHub inventory."""
        if not path.exists():
            logger.warning(f"   ⚠️ Inventory not found: {path}")
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Handle list vs dict wrapper
        items = raw_data if isinstance(raw_data, list) else raw_data.get("projects", [])
        
        # Deduplicate by URL
        seen_urls = set()
        unique = []
        for item in items:
            url = item.get('url', '').lower()
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(RepoInventoryItem(**item))
        
        return unique
    
    def _load_github_inventory_as_map(self, path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Load GitHub inventory as lookup map.
        
        Returns:
            Dict mapping {github_url_lowercase: repo_metadata}
        """
        repos = self._load_github_inventory(path)
        return {
            repo.url.lower().rstrip('/'): {
                'url': repo.url,
                'name': repo.name,
                'visibility': repo.visibility,
                'updatedAt': repo.updatedAt
            }
            for repo in repos
        }
    
    def _load_exclusions(self) -> List[str]:
        """
        Load EXCLUSION_LIST_V1.yaml.
        
        Returns:
            List of repo names to exclude (lowercase)
        """
        try:
            import yaml
            exclusion_path = self.settings.get_governance_path(
                "registry/projects/EXCLUSION_LIST_V1.yaml"
            )
            if not exclusion_path.exists():
                return []
            
            with open(exclusion_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            exclusions = []
            for item in data.get('exclusions', []):
                repo_name = item.get('repo', '').lower()
                if repo_name:
                    exclusions.append(repo_name)
            
            return exclusions
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load exclusions: {e}")
            return []
    
    def _is_excluded(self, github_url: str, exclusions: List[str]) -> bool:
        """Check if a GitHub URL matches any exclusion."""
        if not github_url or not exclusions:
            return False
        
        # Extract repo name from URL
        # https://github.com/Kryssie6985/kiss -> kiss
        parts = github_url.rstrip('/').split('/')
        if len(parts) >= 2:
            repo_name = parts[-1].lower()
            return repo_name in exclusions
        
        return False
    
    def _load_cmp_data(self) -> List[Dict[str, Any]]:
        """
        Load CMP projects from database via scanner.
        
        CMP is the CROWN TRUTH - this is the master source.
        Falls back to canonical_projects_uuids.json if CMP is unreachable.
        """
        # Try live CMP database first
        try:
            from omni.scanners.database.cmp_projects import scan
            result = scan(self.infra_root)
            items = result.get('items', [])
            if items:
                logger.info(f"   📡 CMP live query returned {len(items)} projects")
                return items
            else:
                logger.warning("   ⚠️ CMP query returned 0 items")
        except Exception as e:
            logger.warning(f"   ⚠️ CMP live query failed: {e}")
        
        # FALLBACK: Use canonical_projects_uuids.json (cached CMP mirror)
        logger.info("   🔄 Falling back to canonical_projects_uuids.json")
        return self._load_canonical_fallback()
    
    def _load_canonical_fallback(self) -> List[Dict[str, Any]]:
        """
        Load project data from canonical_projects_uuids.json.
        
        This file IS a CMP mirror — it contains UUIDs, names, keys,
        github_urls, types, and statuses. When CMP is unreachable,
        this is the next best truth.
        
        Returns:
            List of project dicts in the same format as CMP scanner output.
        """
        try:
            canonical_path = self.settings.get_governance_path(
                "registry/uuid/canonical_projects_uuids.json"
            )
            if not canonical_path.exists():
                logger.error("   ❌ canonical_projects_uuids.json not found!")
                return []
            
            with open(canonical_path, 'r', encoding='utf-8') as f:
                canonical = json.load(f)
            
            # Transform canonical format to match CMP scanner output format
            projects = []
            for uuid, meta in canonical.get('uuids', {}).items():
                projects.append({
                    'uuid': uuid,
                    'name': meta.get('name', ''),
                    'key': meta.get('key', ''),
                    'type': meta.get('type', 'project'),
                    'status': meta.get('status', 'active'),
                    'github_url': meta.get('github_url'),
                    'domain': meta.get('domain'),
                })
            
            logger.info(
                f"   ✅ Loaded {len(projects)} projects from canonical fallback "
                f"({sum(1 for p in projects if p.get('github_url'))} with github_url)"
            )
            return projects
            
        except Exception as e:
            logger.error(f"   ❌ Canonical fallback also failed: {e}")
            return []
    
    def _load_legacy_oracle(self) -> Dict[str, str]:
        """
        Load canonical UUIDs from CMP-based registry.
        
        CROWN TRUTH: canonical_projects_uuids.json is mirrored from CMP database.
        This replaces the old drifted PROJECT_REGISTRY_MASTER.md.
        
        Returns:
            Dict mapping { project_name_lowercase: uuid }
        """
        try:
            canonical_path = self.settings.get_governance_path(
                "registry/uuid/canonical_projects_uuids.json"
            )
            if not canonical_path.exists():
                logger.warning("   ⚠️ Canonical registry not found, run: python -m tools.omni.omni.core.canonical_uuid_builder")
                return {}
            
            with open(canonical_path, 'r', encoding='utf-8') as f:
                canonical = json.load(f)
            
            # Build name -> uuid mapping
            uuid_map = {}
            for uuid, metadata in canonical.get('uuids', {}).items():
                name = metadata.get('name', '').lower()
                key = metadata.get('key', '').lower()
                
                # Map both name and key to UUID
                if name:
                    uuid_map[name] = uuid
                if key and key != name:
                    uuid_map[key] = uuid
            
            logger.info(f"   📡 Loaded {len(uuid_map)} canonical UUIDs from CMP mirror")
            return uuid_map
            
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load canonical oracle: {e}")
            return {}
    
    def _load_overrides(self) -> Dict[str, Dict]:
        """
        Load local overrides manifest and build lookup map.
        Handles aliases by duplicating the override entry for each alias key.
        """
        try:
            import yaml
            path = self.settings.get_registry_overrides_path()
            if not path.exists():
                return {}
            
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            overrides = {}
            for item in data.get('overrides', []):
                # Normalize canonical URL
                url = item.get('github_url', '').lower().rstrip('/')
                if not url:
                    continue
                
                # Store canonical entry
                overrides[url] = item
                
                # Store alias entries pointing to same data
                for alias in item.get('aliases', []):
                    alias_url = alias.lower().rstrip('/')
                    overrides[alias_url] = item  # Point alias to same override config
            
            return overrides
            
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to load overrides: {e}")
            return {}

    def _scan_heart_integration(self) -> Dict[str, int]:
        """
        Scan which project directories contain federation_heart imports.
        
        Uses ripgrep for speed. Maps project local_path -> import count.
        
        Returns:
            Dict of { 'local_path_lowercase_fwd_slash': import_file_count }
        """
        try:
            result = subprocess.run(
                ["rg", "-l", "--no-ignore", "-g", "*.py",
                 "from federation_heart", str(self.infra_root)],
                capture_output=True, encoding="utf-8", errors="replace",
                timeout=30
            )
            
            if result.returncode not in (0, 1):  # 1 = no matches (fine)
                logger.debug(f"   ripgrep returned code {result.returncode}")
                return {}
            
            # Collect all files that import federation_heart
            heart_files = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    try:
                        rel = str(
                            Path(line).relative_to(self.infra_root)
                        ).replace("\\", "/").lower()
                        heart_files.append(rel)
                    except ValueError:
                        pass
            
            # Now load the registry's known local_paths to map files -> projects
            # We need to read from our settings to get all project paths
            import yaml
            registry_path = self.settings.get_governance_path(
                "registry/projects/PROJECT_REGISTRY_V1.yaml"
            )
            
            # Build a lookup from directory -> project_path
            # Using the local_path_map from _scan_local_paths would be circular,
            # so we use the current CMP data's github URLs mapped to local paths
            # Instead, let's directly map: for each heart_file, find which 
            # known workspace directory it belongs to
            
            # Get all workspace roots
            try:
                from omni.config.settings import get_all_workspaces
                scan_roots = get_all_workspaces()
            except ImportError:
                scan_roots = [self.infra_root]
            
            # Find all git repos to build a path -> project_dir map
            from omni.scanners.git.git import _find_git_repos
            project_dirs = set()
            for root in scan_roots:
                if root.exists():
                    for repo_path in _find_git_repos(root):
                        try:
                            rel = str(
                                repo_path.relative_to(self.infra_root)
                            ).replace("\\", "/").lower()
                            project_dirs.add(rel)
                        except ValueError:
                            pass
            
            # Map: for each project dir, count how many heart-importing files it contains
            path_to_count: Dict[str, int] = {}
            for hf in heart_files:
                # Skip federation_heart itself — it IS the heart
                if hf.startswith("federation_heart/"):
                    continue
                    
                # Find the longest matching project dir
                best_dir = None
                best_len = 0
                for pd in project_dirs:
                    if hf.startswith(pd + "/") and len(pd) > best_len:
                        best_dir = pd
                        best_len = len(pd)
                
                if best_dir:
                    path_to_count[best_dir] = path_to_count.get(best_dir, 0) + 1
            
            logger.info(f"   🔍 Heart scan: {len(heart_files)} files import Heart, across {len(path_to_count)} project dirs")
            return path_to_count
            
        except FileNotFoundError:
            logger.warning("   ⚠️ ripgrep (rg) not found, skipping heart integration scan")
            return {}
        except Exception as e:
            logger.warning(f"   ⚠️ Heart integration scan failed: {e}")
            return {}

    def _scan_local_paths(self) -> Dict[str, str]:
        """
        Scan local filesystem for git repos and map GitHub URLs to paths.
        
        Returns:
            Dict of { 'github_url_lowercase': 'local_path' }
        """
        try:
            from omni.scanners.git.git import scan_local_paths
            return scan_local_paths()
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to scan local paths: {e}")
            return {}
    
    def _find_local_only_projects(
        self,
        known_github_urls: set
    ) -> List[RegistryProject]:
        """Find projects that exist locally but not on GitHub."""
        # TODO: Implement local project discovery
        # Scan stations/, agents/, etc. for projects without GitHub remotes
        return []


def build_registry(
    inventory_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    include_local_only: bool = True
) -> Path:
    """
    Convenience function to build and save registry.
    
    Returns path to saved registry file.
    """
    builder = RegistryBuilder()
    registry = builder.build(inventory_path, include_local_only)
    return builder.save(registry, output_path)
