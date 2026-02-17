"""
Federation Heart Health Scanner
Queries FederationCore for runtime status and pillar health
"""
from pathlib import Path
from typing import Dict, Any
import sys


def scan(target: Path) -> dict:
    """
    Query FederationCore for runtime health status.
    
    Args:
        target: Path to Infrastructure root (or anywhere in Federation)
        
    Returns:
        dict with FederationCore status, pillar health, and component availability
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "federation_health",
            "version": "1.0.0"
        },
        "summary": {
            "status": "UNKNOWN",
            "pillars_active": 0,
            "pillars_total": 5,
            "components_healthy": []
        }
    }
    
    try:
        # Add federation_heart to path
        infra_root = find_infrastructure_root(target)
        if not infra_root:
            results["metadata"]["error"] = "Infrastructure root not found"
            return results
        
        # Try importing FederationCore
        try:
            from federation_heart.core.federation_core import FederationCore
            
            # Initialize core
            core = FederationCore()
            
            # Get status
            status = core.status()
            
            # Extract health info
            health_info = {
                "core_status": status.get("component", "UNKNOWN"),
                "state": status.get("state", "UNKNOWN"),
                "pillars": {}
            }
            
            # Check each pillar
            pillar_names = ["cartography", "connectivity", "constitution", "foundry", "consciousness"]
            pillars_active = 0
            
            for pillar_name in pillar_names:
                pillar_status = status.get(pillar_name, "UNKNOWN")
                health_info["pillars"][pillar_name] = pillar_status
                if pillar_status in ["ACTIVE", "SECURE"]:
                    pillars_active += 1
            
            # Update summary
            results["summary"]["status"] = health_info["state"]
            results["summary"]["pillars_active"] = pillars_active
            results["summary"]["components_healthy"] = [
                p for p, s in health_info["pillars"].items() 
                if s in ["ACTIVE", "SECURE"]
            ]
            
            # Add to items
            results["items"].append(health_info)
            results["count"] = 1
            
        except ImportError as e:
            results["metadata"]["error"] = f"FederationCore not available: {str(e)}"
            results["summary"]["status"] = "NOT_INSTALLED"
            
    except Exception as e:
        results["metadata"]["error"] = f"Federation health check failed: {str(e)}"
        results["summary"]["status"] = "ERROR"
    
    return results


def find_infrastructure_root(start_path: Path) -> Path:
    """Find Infrastructure root by looking for federation_heart/."""
    current = start_path if start_path.is_dir() else start_path.parent
    
    # Walk up until we find federation_heart or hit root
    for _ in range(10):  # Safety limit
        if (current / "federation_heart").exists():
            return current
        
        parent = current.parent
        if parent == current:  # Hit filesystem root
            break
        current = parent
    
    return None


def get_detailed_health() -> Dict[str, Any]:
    """
    Get detailed health metrics from FederationCore.
    
    Returns comprehensive status including:
    - All pillar detailed_status()
    - Component availability
    - Service health
    """
    try:
        from federation_heart.core.federation_core import FederationCore
        from federation_heart.pillars import (
            CartographyPillar,
            ConnectivityPillar,
            ConstitutionPillar,
            FoundryPillar
        )
        
        core = FederationCore()
        
        detailed = {
            "core": core.status(),
            "pillars": {}
        }
        
        # Get detailed status from each pillar
        try:
            detailed["pillars"]["cartography"] = CartographyPillar().detailed_status()
        except Exception as e:
            detailed["pillars"]["cartography"] = {"error": str(e)}
        
        try:
            detailed["pillars"]["connectivity"] = ConnectivityPillar().detailed_status()
        except Exception as e:
            detailed["pillars"]["connectivity"] = {"error": str(e)}
        
        try:
            detailed["pillars"]["constitution"] = ConstitutionPillar().detailed_status()
        except Exception as e:
            detailed["pillars"]["constitution"] = {"error": str(e)}
        
        try:
            detailed["pillars"]["foundry"] = FoundryPillar().detailed_status()
        except Exception as e:
            detailed["pillars"]["foundry"] = {"error": str(e)}
        
        return detailed
        
    except Exception as e:
        return {"error": f"Failed to get detailed health: {str(e)}"}
