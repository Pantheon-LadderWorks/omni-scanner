"""
Pillar Health Scanner
Queries all 5 Federation Heart pillars for detailed status
"""
from pathlib import Path
from typing import Dict, Any


def scan(target: Path) -> dict:
    """
    Query all Federation Heart pillars for health status.
    
    Args:
        target: Path to Infrastructure root (or anywhere in Federation)
        
    Returns:
        dict with status of all 5 pillars and their components
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "pillar_health",
            "version": "1.0.0"
        },
        "summary": {
            "pillars_active": 0,
            "pillars_total": 5,
            "overall_health": "UNKNOWN",
            "components_healthy": []
        }
    }
    
    try:
        # Try importing all pillars
        try:
            from federation_heart.pillars import (
                CartographyPillar,
                ConnectivityPillar,
                ConstitutionPillar,
                FoundryPillar
            )
            
            # ConsciousnessPillar may not exist yet
            try:
                from federation_heart.pillars import ConsciousnessPillar
                has_consciousness = True
            except ImportError:
                ConsciousnessPillar = None
                has_consciousness = False
            
            health_info = {
                "pillars": {},
                "overall_status": "CHECKING"
            }
            
            pillars_to_check = [
                ("cartography", CartographyPillar),
                ("connectivity", ConnectivityPillar),
                ("constitution", ConstitutionPillar),
                ("foundry", FoundryPillar)
            ]
            
            if has_consciousness and ConsciousnessPillar:
                pillars_to_check.append(("consciousness", ConsciousnessPillar))
            
            # Update total count based on available pillars
            results["summary"]["pillars_total"] = len(pillars_to_check)
            
            active_count = 0
            healthy_components = []
            
            for pillar_name, PillarClass in pillars_to_check:
                try:
                    pillar = PillarClass()
                    
                    # Get detailed status
                    status = pillar.detailed_status()
                    
                    health_info["pillars"][pillar_name] = {
                        "status": status.get("pillar_status", "UNKNOWN"),
                        "details": status
                    }
                    
                    # Count active
                    if status.get("pillar_status") in ["ACTIVE", "SECURE"]:
                        active_count += 1
                        healthy_components.append(pillar_name)
                    
                except Exception as e:
                    health_info["pillars"][pillar_name] = {
                        "status": "ERROR",
                        "error": str(e)
                    }
            
            # Determine overall health (based on active vs total)
            total_pillars = len(pillars_to_check)
            if active_count == total_pillars:
                overall_health = "EXCELLENT"
            elif active_count >= total_pillars - 1:
                overall_health = "GOOD"
            elif active_count >= total_pillars // 2:
                overall_health = "DEGRADED"
            elif active_count >= 1:
                overall_health = "CRITICAL"
            else:
                overall_health = "OFFLINE"
            
            health_info["overall_status"] = overall_health
            
            # Update summary
            results["summary"]["pillars_active"] = active_count
            results["summary"]["overall_health"] = overall_health
            results["summary"]["components_healthy"] = healthy_components
            
            # Add to items
            results["items"].append(health_info)
            results["count"] = 1
            
        except ImportError as e:
            results["metadata"]["error"] = f"Pillars not available: {str(e)}"
            results["summary"]["overall_health"] = "NOT_INSTALLED"
            
    except Exception as e:
        results["metadata"]["error"] = f"Pillar health check failed: {str(e)}"
        results["summary"]["overall_health"] = "ERROR"
    
    return results


def get_pillar_details(pillar_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific pillar.
    
    Args:
        pillar_name: Name of pillar (cartography, connectivity, etc.)
        
    Returns:
        Detailed pillar status and component information
    """
    try:
        from federation_heart import pillars
        
        pillar_classes = {
            "cartography": pillars.CartographyPillar,
            "connectivity": pillars.ConnectivityPillar,
            "constitution": pillars.ConstitutionPillar,
            "foundry": pillars.FoundryPillar,
            "consciousness": pillars.ConsciousnessPillar
        }
        
        if pillar_name not in pillar_classes:
            return {"error": f"Unknown pillar: {pillar_name}"}
        
        PillarClass = pillar_classes[pillar_name]
        pillar = PillarClass()
        
        return {
            "name": pillar_name,
            "status": pillar.detailed_status(),
            "description": get_pillar_description(pillar_name)
        }
        
    except Exception as e:
        return {"error": f"Failed to get pillar details: {str(e)}"}


def get_pillar_description(pillar_name: str) -> str:
    """Get human-readable description of pillar purpose."""
    descriptions = {
        "cartography": "WHERE things are - Path resolution, registry navigation, ecosystem mapping",
        "connectivity": "HOW to connect - Station routing, orchestration, tunnels",
        "constitution": "WHAT the rules are - Governance, contracts, policies",
        "foundry": "HOW things are made - Template instantiation, artifact creation",
        "consciousness": "WHO we are - Agent identity, emergence detection"
    }
    return descriptions.get(pillar_name, "Unknown pillar")


def get_pillar_health_matrix() -> Dict[str, Any]:
    """
    Get comprehensive health matrix for all pillars.
    
    Returns:
        Matrix showing status of each pillar and cross-dependencies
    """
    try:
        from federation_heart.pillars import (
            CartographyPillar,
            ConnectivityPillar,
            ConstitutionPillar,
            FoundryPillar,
            ConsciousnessPillar
        )
        
        matrix = {
            "pillars": {},
            "dependencies": {},
            "health_score": 0.0
        }
        
        pillars = {
            "cartography": CartographyPillar(),
            "connectivity": ConnectivityPillar(),
            "constitution": ConstitutionPillar(),
            "foundry": FoundryPillar(),
            "consciousness": ConsciousnessPillar()
        }
        
        total_score = 0
        for name, pillar in pillars.items():
            try:
                status = pillar.detailed_status()
                pillar_status = status.get("pillar_status", "UNKNOWN")
                
                # Score: ACTIVE=1.0, SECURE=1.0, DEGRADED=0.5, others=0
                score = 1.0 if pillar_status in ["ACTIVE", "SECURE"] else 0.5 if pillar_status == "DEGRADED" else 0.0
                total_score += score
                
                matrix["pillars"][name] = {
                    "status": pillar_status,
                    "score": score,
                    "components": status
                }
            except Exception as e:
                matrix["pillars"][name] = {
                    "status": "ERROR",
                    "score": 0.0,
                    "error": str(e)
                }
        
        # Calculate overall health score (0.0 to 1.0)
        matrix["health_score"] = total_score / len(pillars)
        
        # Document known dependencies
        matrix["dependencies"] = {
            "connectivity": ["cartography"],  # Needs paths/registry
            "foundry": ["cartography", "constitution"],  # Needs paths and templates
            "consciousness": ["cartography", "constitution"]  # Needs identity and rules
        }
        
        return matrix
        
    except Exception as e:
        return {"error": f"Failed to generate health matrix: {str(e)}"}
