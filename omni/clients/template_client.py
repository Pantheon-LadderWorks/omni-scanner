"""
Template Client - Generic Interface for Omni Scanners
=====================================================

Use this template to create your own "Station" or "Client" that orchestrates
Omni scanners for your specific workflow.

Pattern:
1. Initialize with Omni root (auto-detection provided).
2. Define semantic methods (e.g., `audit_security`, `optimize_images`).
3. Import `omni.scanners.SCANNERS` locally to avoid circular imports.
4. Orchestrate the scanners and return a standardized dictionary.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# Configure logger for your client
logger = logging.getLogger("Omni.Clients.Template")

class TemplateClient:
    """
    Template for creating custom Omni orchestration clients.
    
    Replace this docstring with your client's purpose.
    Example: "SecurityClient - Orchestrates vulnerability scans."
    """
    
    def __init__(self, omni_root: Optional[Path] = None):
        """
        Initialize the client.
        
        Args:
            omni_root: Path to Omni root. If None, verification of install location is performed.
        """
        self.omni_root = omni_root or self._find_omni_root()
        
    def _find_omni_root(self) -> Path:
        """
        Auto-detect Omni installation. 
        Standard logic to find the tool root relative to this file or cwd.
        """
        # Common locations to check
        candidates = [
            Path(__file__).parent.parent.parent,  # tools/omni/omni/clients -> tools/omni
            Path.cwd() / "tools" / "omni",
            Path.cwd(),
        ]
        
        for candidate in candidates:
            if (candidate / "omni").exists():
                return candidate
        
        # Fallback to relative path from this file
        return Path(__file__).parent.parent.parent

    def run_example_workflow(self, target: Path, dry_run: bool = False) -> Dict[str, Any]:
        """
        Example semantic workflow: "Health Check".
        
        Args:
            target: Directory to scan.
            dry_run: If True, simulate the action.
            
        Returns:
            Standardized result dictionary.
        """
        # 1. Handle Dry Run
        if dry_run:
            logger.info(f"[DRY RUN] Would scan {target}")
            return {
                "success": True,
                "dry_run": True,
                "operation": "example_workflow",
            }

        try:
            # 2. Lazy Import Scanners (Best Practice)
            # Importing here prevents circular dependency issues during initialization
            from omni.scanners import SCANNERS
            
            logger.info(f"🚀 Starting Health Check for {target}")
            
            results = {}
            
            # 3. Run Specific Scanners
            # Check availability before running to be robust
            
            # Example: Run 'health/system' scanner
            if "health/system" in SCANNERS:
                logger.info("   Running System Health Scan...")
                # Call the scanner function directly
                results["system"] = SCANNERS["health/system"](str(target))
            else:
                logger.warning("   'health/system' scanner not found.")
                results["system"] = {"error": "scanner_not_found"}

            # Example: Run 'static/deps' scanner
            if "static/deps" in SCANNERS:
                logger.info("   Running Dependencies Scan...")
                results["deps"] = SCANNERS["static/deps"](str(target))
                
            # 4. Standardize Output
            return {
                "success": True,
                "operation": "example_workflow",
                "target": str(target),
                "scanners_run": list(results.keys()),
                "results": results,
            }

        except Exception as e:
            # 5. Robust Error Handling
            logger.error(f"Workflow failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "example_workflow",
            }
