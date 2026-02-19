"""
omni/scanners/__init__.py
The Scanner Registry
=====================
Dynamically loads scanners from subdirectories based on SCANNER_MANIFEST.yaml.

Structure:
  scanners/
  ├── architecture/ (coupling & design analysis)
  ├── discovery/    (project & mcp structure)
  ├── database/     (generic sql/postgres)
  ├── git/          (repository operations)
  ├── health/       (system & runtime health)
  ├── library/      (content taxonomy)
  ├── phoenix/      (resurrection & archives)
  ├── polyglot/     (language-specific analysis)
  ├── search/       (text & file patterns)
  └── static/       (filesystem analysis)

Each category has a SCANNER_MANIFEST.yaml that declares available scanners.
"""
import yaml
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, Callable, List

logger = logging.getLogger("Omni.Scanners")

# The Flat Registry for CLI compatibility: { 'scanner_name': scan_function }
SCANNERS: Dict[str, Callable] = {}

# The Categorized Registry: { 'category': { 'name': scan_function } }
SCANNER_CATEGORIES: Dict[str, Dict[str, Callable]] = {}

# Metadata for each scanner
SCANNER_META: Dict[str, Dict[str, Any]] = {}


def load_scanners() -> None:
    """
    Walks the scanners directory, finds SCANNER_MANIFEST.yaml files,
    and imports the declared scanner modules.
    """
    root_dir = Path(__file__).parent
    skip_dirs = {"__pycache__"}
    
    for category_dir in root_dir.iterdir():
        if not category_dir.is_dir():
            continue
        if category_dir.name in skip_dirs:
            continue
            
        manifest_path = category_dir / "SCANNER_MANIFEST.yaml"
        
        if not manifest_path.exists():
            continue
            
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = yaml.safe_load(f)
                
            category = manifest.get('category', category_dir.name)
            SCANNER_CATEGORIES[category] = {}
            
            for entry in manifest.get('scanners', []):
                scanner_name = entry.get('name')
                module_file = entry.get('file')
                func_name = entry.get('function', 'scan')
                
                if not scanner_name or not module_file:
                    continue
                
                # Dynamic Import: omni.scanners.static.surfaces
                module_name = f"omni.scanners.{category_dir.name}.{module_file.replace('.py', '')}"
                
                try:
                    mod = importlib.import_module(module_name)
                    
                    if hasattr(mod, func_name):
                        scanner_func = getattr(mod, func_name)
                        
                        # Register in flat registry (for CLI compatibility)
                        SCANNERS[scanner_name] = scanner_func
                        
                        # Register in categorized registry
                        SCANNER_CATEGORIES[category][scanner_name] = scanner_func
                        
                        # Store metadata
                        SCANNER_META[scanner_name] = {
                            "category": category,
                            "file": module_file,
                            "function": func_name,
                            "description": entry.get('description', ''),
                            "module": module_name,
                        }
                    else:
                        logger.warning(f"Scanner {module_name} missing function '{func_name}'")
                        
                except ImportError as e:
                    logger.debug(f"Failed to import scanner {module_name}: {e}")

        except Exception as e:
            logger.error(f"Error loading manifest for {category_dir.name}: {e}")


def get_scanners_by_category(category: str) -> Dict[str, Callable]:
    """Get all scanners in a category."""
    return SCANNER_CATEGORIES.get(category, {})


def get_scanner_meta(name: str) -> Dict[str, Any]:
    """Get metadata for a scanner."""
    return SCANNER_META.get(name, {})


def list_categories() -> List[str]:
    """List all scanner categories."""
    return list(SCANNER_CATEGORIES.keys())


# Auto-load on import
load_scanners()
