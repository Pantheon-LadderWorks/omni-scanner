"""
omni/pillars/gatekeeper.py
The Gatekeeper Pillar - The Guard
=================================
Responsibility:
1.  Policy enforcement (gate checks)
2.  UUID provenance auditing
3.  Compliance validation

Absorbs: core/gate.py, core/provenance.py
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("Omni.Pillar.Gatekeeper")


class GatekeeperPillar:
    """
    The Gatekeeper Pillar - enforces policy and audits provenance.
    """
    
    def __init__(self, settings_module):
        self.settings = settings_module
        self.heart_available = self.settings.heart_available()
        
        logger.info("🛡️ Gatekeeper Pillar initialized")
    
    # =========================================================================
    # Policy Enforcement (from core/gate.py)
    # =========================================================================
    
    def check_gate(
        self, 
        scan_data: Dict[str, Any], 
        strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Evaluates scan data against policy.
        
        Args:
            scan_data: Results from a scan operation
            strict: If True, fail on warnings
            
        Returns:
            Tuple of (passed: bool, messages: List[str])
        """
        # Delegate to core gate logic
        from omni.core.gate import check
        return check(scan_data, strict=strict)
    
    # =========================================================================
    # Provenance Auditing (from core/provenance.py)
    # =========================================================================
    
    def audit_provenance(
        self,
        target_path: Path = None,
        canonical_uuids: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Audit UUID provenance across the federation.
        
        Scans files for UUID references and validates against canonical sources.
        
        Args:
            target_path: Path to audit (defaults to infrastructure root)
            canonical_uuids: Known good UUIDs (defaults to fetching from DB)
            
        Returns:
            Audit report with findings
        """
        if target_path is None:
            target_path = self.settings.get_infrastructure_root()
        
        logger.info(f"🔍 Starting provenance audit: {target_path}")
        
        # Delegate to core provenance logic
        from omni.core.provenance import run_provenance_audit
        
        # The provenance module has its own entry point
        # We wrap it here to provide pillar-level interface
        try:
            # Note: run_provenance_audit is currently a standalone function
            # that writes its own output. Future refactor should make it
            # return data instead.
            run_provenance_audit()
            return {"status": "completed", "path": str(target_path)}
        except Exception as e:
            logger.error(f"❌ Provenance audit failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def validate_uuid(self, uuid_str: str) -> Dict[str, Any]:
        """
        Validate a single UUID against canonical sources.
        
        Args:
            uuid_str: UUID string to validate
            
        Returns:
            Validation result with source info
        """
        import re
        
        # Basic format check
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(uuid_str):
            return {
                "valid": False,
                "error": "Invalid UUID format"
            }
        
        # Check if it's a known canonical UUID
        # TODO: Integrate with fetcher to check CMP database
        return {
            "valid": True,
            "format_check": "passed",
            "canonical_check": "not_implemented"
        }
    
    # =========================================================================
    # Compliance Checks
    # =========================================================================
    
    def check_documentation_compliance(
        self, 
        project_path: Path
    ) -> Dict[str, Any]:
        """
        Check if a project has required documentation.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Compliance report
        """
        required_docs = ["README.md", "CHANGELOG.md"]
        optional_docs = ["ARCHITECTURE.md", "CONTRIBUTING.md", "LICENSE"]
        
        findings = {
            "required": {},
            "optional": {},
            "compliant": True
        }
        
        for doc in required_docs:
            exists = (project_path / doc).exists()
            findings["required"][doc] = exists
            if not exists:
                findings["compliant"] = False
        
        for doc in optional_docs:
            findings["optional"][doc] = (project_path / doc).exists()
        
        return findings
    
    def check_surface_coverage(
        self,
        scan_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check contract surface coverage from scan results.
        
        Args:
            scan_result: Results from surface scan
            
        Returns:
            Coverage report
        """
        surfaces = scan_result.get("findings", {}).get("surfaces", {})
        items = surfaces.get("items", [])
        
        total = len(items)
        found = sum(1 for s in items if s.get("status") == "found")
        missing = sum(1 for s in items if s.get("status") == "missing")
        
        return {
            "total_surfaces": total,
            "found": found,
            "missing": missing,
            "coverage_percent": (found / total * 100) if total > 0 else 100
        }
