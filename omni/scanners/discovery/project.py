"""
omni/scanners/discovery/project.py
Project Scanner - Thin Wrapper
==============================
Scans and builds the PROJECT_REGISTRY_V1.yaml.

This is a THIN WRAPPER - it just calls registry_builder.
The heavy lifting is in omni/builders/registry_builder.py.

Usage:
    omni scan project              # Build registry from defaults
    omni scan project --output=.   # Output to current directory
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from omni.core.model import ScanResult

logger = logging.getLogger("Omni.Scanner.Project")


def scan(target_path: Path) -> ScanResult:
    """
    Build the PROJECT_REGISTRY_V1.yaml.
    
    This scanner:
    1. Loads GitHub inventory
    2. Resolves identities via identity_engine
    3. Generates PROJECT_REGISTRY_V1.yaml
    
    Args:
        target_path: Ignored (uses governance paths)
        
    Returns:
        ScanResult with registry build status
    """
    logger.info("📦 Project Registry Scanner starting...")
    
    try:
        from omni.builders.registry_builder import RegistryBuilder
        
        # Build the registry
        builder = RegistryBuilder()
        registry = builder.build()
        
        # Save to canonical location
        output_path = builder.save(registry)
        
        return ScanResult(
            target=str(target_path),
            version="0.1",
            timestamp=datetime.now().isoformat(),
            findings={
                "registry": {
                    "path": str(output_path),
                    "version": registry.version,
                    "stats": registry.stats,
                    "project_count": len(registry.projects)
                }
            },
            summary={
                "count": registry.stats["total"],
                "github": registry.stats["github"],
                "linked": registry.stats["linked"],
                "status": "success"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Project scan failed: {e}")
        return ScanResult(
            target=str(target_path),
            version="0.1",
            timestamp=datetime.now().isoformat(),
            findings={"error": str(e)},
            summary={"status": "error", "count": 0}
        )
