"""
omni/pillars/registry.py
The Registry Pillar - The Law
=============================
Responsibility:
1.  Parse governance manifests
2.  Load and validate registries
3.  Manage registry events/schemas

Absorbs: core/registry.py, core/registry_v2.py, core/registry_events.py
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("Omni.Pillar.Registry")


class RegistryPillar:
    """
    The Registry Pillar - parses and validates Federation registries.
    """
    
    def __init__(self, settings_module):
        self.settings = settings_module
        self.heart_available = self.settings.heart_available()
        
        # Cache for loaded registries
        self._cache: Dict[str, Any] = {}
        
        logger.info("📜 Registry Pillar initialized")
    
    # =========================================================================
    # Manifest Loading (Delegates to core/registry.py logic)
    # =========================================================================
    
    def load_master_registry(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load the master project registry.
        
        Returns:
            Dict with project data keyed by normalized path
        """
        cache_key = "master_registry"
        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Import the parsing logic from core
        from omni.core.registry import parse_master_registry_md, parse_final_yaml_registry
        
        result = {}
        
        # Load MD format
        md_path = self.settings.get_governance_path("registry/projects/PROJECT_REGISTRY_MASTER.md")
        if md_path.exists():
            result.update(parse_master_registry_md(md_path))
        
        # Load YAML format
        yaml_path = self.settings.get_governance_path("registry/projects/PANTHEON_PROJECT_REGISTRY.final.yaml")
        if yaml_path.exists():
            result.update(parse_final_yaml_registry(yaml_path))
        
        self._cache[cache_key] = result
        logger.info(f"📜 Loaded master registry: {len(result)} entries")
        return result
    
    def load_cmp_registry(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load the CMP project registry.
        
        Returns:
            Full registry dict with 'projects' list
        """
        cache_key = "cmp_registry"
        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]
        
        import yaml
        
        cmp_path = self.settings.get_cmp_registry_path()
        if not cmp_path or not cmp_path.exists():
            logger.warning("⚠️ CMP registry not found")
            return {"projects": []}
        
        with open(cmp_path, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f) or {"projects": []}
        
        self._cache[cache_key] = result
        logger.info(f"📜 Loaded CMP registry: {len(result.get('projects', []))} projects")
        return result
    
    def load_station_registry(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        Load the station registry.
        
        Returns:
            List of station configurations
        """
        cache_key = "station_registry"
        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]
        
        if not self.heart_available:
            logger.warning("⚠️ Heart unavailable - station registry not accessible")
            return []
        
        try:
            result = self.settings.cartography.list_stations()
            self._cache[cache_key] = result
            logger.info(f"📜 Loaded station registry: {len(result)} stations")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to load station registry: {e}")
            return []
    
    def load_agent_registry(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        Load the agent registry (Council UUID Registry).
        
        Returns:
            List of agent configurations
        """
        cache_key = "agent_registry"
        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]
        
        if not self.heart_available:
            logger.warning("⚠️ Heart unavailable - agent registry not accessible")
            return []
        
        try:
            result = self.settings.cartography.list_agents()
            self._cache[cache_key] = result
            logger.info(f"📜 Loaded agent registry: {len(result)} agents")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to load agent registry: {e}")
            return []
    
    # =========================================================================
    # Registry Validation
    # =========================================================================
    
    def validate_registry(self, registry_type: str) -> List[str]:
        """
        Validate a registry for schema compliance.
        
        Args:
            registry_type: One of 'master', 'cmp', 'station', 'agent'
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if registry_type == "master":
            data = self.load_master_registry()
            # Basic validation
            if not data:
                errors.append("Master registry is empty")
        
        elif registry_type == "cmp":
            data = self.load_cmp_registry()
            if "projects" not in data:
                errors.append("CMP registry missing 'projects' key")
        
        elif registry_type == "station":
            data = self.load_station_registry()
            for station in data:
                if "id" not in station:
                    errors.append(f"Station missing 'id': {station}")
        
        elif registry_type == "agent":
            data = self.load_agent_registry()
            for agent in data:
                if "static_uuid" not in agent:
                    errors.append(f"Agent missing 'static_uuid': {agent.get('key', 'unknown')}")
        
        else:
            errors.append(f"Unknown registry type: {registry_type}")
        
        return errors
    
    # =========================================================================
    # Cache Management
    # =========================================================================
    
    def clear_cache(self):
        """Clear all cached registry data."""
        self._cache.clear()
        logger.info("📜 Registry cache cleared")
