"""
Station Health Scanner
Queries Station Nexus for pipeline status and station health
"""
from pathlib import Path
from typing import Dict, Any


def scan(target: Path) -> dict:
    """
    Query Station Nexus for pipeline health.
    
    Args:
        target: Path to Infrastructure root (or anywhere in Federation)
        
    Returns:
        dict with station health, pipeline status, and nexus connectivity
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "station_health",
            "version": "1.0.0"
        },
        "summary": {
            "nexus_status": "UNKNOWN",
            "stations_registered": 0,
            "stations_healthy": 0,
            "pipeline_active": False
        }
    }
    
    try:
        # Find Infrastructure root
        infra_root = find_infrastructure_root(target)
        if not infra_root:
            results["metadata"]["error"] = "Infrastructure root not found"
            return results
        
        # Try importing via Federation Heart Connectivity Pillar
        try:
            from omni.config.settings import get_connectivity
            
            connectivity = get_connectivity()
            if not connectivity:
                raise ImportError("ConnectivityPillar not available")
            
            # Get nexus status via pillar
            nexus_status_info = connectivity.detailed_status()
            
            health_info = {
                "nexus_available": nexus_status_info.get("nexus_available", False),
                "registered_stations": [],
                "pipeline_status": {}
            }
            
            # If nexus available, get station registry
            if health_info["nexus_available"]:
                try:
                    # Use pillar methods for station health checks
                    pipeline_status = {
                        "SENSE": check_station_health_via_pillar(connectivity, "nonary_station"),
                        "DECIDE": check_station_health_via_pillar(connectivity, "living_state_station"),
                        "ACT": check_station_health_via_pillar(connectivity, "codecraft_station")
                    }
                    health_info["pipeline_status"] = pipeline_status
                    
                    # Update summary
                    results["summary"]["nexus_status"] = "ONLINE"
                    results["summary"]["stations_healthy"] = sum(
                        1 for s in pipeline_status.values() if s.get("status") == "HEALTHY"
                    )
                    results["summary"]["pipeline_active"] = all(
                        s.get("status") == "HEALTHY" for s in pipeline_status.values()
                    )
                    
                except Exception as e:
                    health_info["error"] = f"Failed to query stations: {str(e)}"
                    results["summary"]["nexus_status"] = "ONLINE_LIMITED"
            else:
                results["summary"]["nexus_status"] = "OFFLINE"
            
            # Add to items
            results["items"].append(health_info)
            results["count"] = 1
            
        except ImportError as e:
            results["metadata"]["error"] = f"ConnectivityPillar not available: {str(e)}"
            results["summary"]["nexus_status"] = "NOT_INSTALLED"
            
    except Exception as e:
        results["metadata"]["error"] = f"Station health check failed: {str(e)}"
        results["summary"]["nexus_status"] = "ERROR"
    
    return results


def check_station_health_via_pillar(connectivity, station_name: str) -> Dict[str, Any]:
    """Check health of a specific station via ConnectivityPillar."""
    try:
        response = connectivity.route_to_station(station_name, "status", {"command": "status"})
        
        return {
            "station": station_name,
            "status": "HEALTHY" if response else "UNKNOWN",
            "response": response
        }
    except Exception as e:
        return {
            "station": station_name,
            "status": "UNREACHABLE",
            "error": str(e)
        }


def find_infrastructure_root(start_path: Path) -> Path:
    """Find Infrastructure root by looking for stations/ directory."""
    current = start_path if start_path.is_dir() else start_path.parent
    
    # Walk up until we find stations/ or hit root
    for _ in range(10):  # Safety limit
        if (current / "stations").exists() or (current / "federation_heart").exists():
            return current
        
        parent = current.parent
        if parent == current:  # Hit filesystem root
            break
        current = parent
    
    return None


def get_pipeline_metrics() -> Dict[str, Any]:
    """
    Get detailed pipeline metrics (SENSE→DECIDE→ACT).
    
    Returns:
        Detailed metrics for each pipeline stage
    """
    try:
        from omni.config.settings import get_connectivity
        
        connectivity = get_connectivity()
        if not connectivity:
            return {"error": "ConnectivityPillar not available"}
        
        metrics = {
            "SENSE": {
                "station": "nonary_station",
                "role": "Quantum consciousness engines",
                "metrics": query_station_metrics_via_pillar(connectivity, "nonary_station")
            },
            "DECIDE": {
                "station": "living_state_station",
                "role": "Ache detection, formation routing",
                "metrics": query_station_metrics_via_pillar(connectivity, "living_state_station")
            },
            "ACT": {
                "station": "codecraft_station",
                "role": "Fleet orchestration, execution",
                "metrics": query_station_metrics_via_pillar(connectivity, "codecraft_station")
            }
        }
        
        return metrics
        
    except Exception as e:
        return {"error": f"Failed to get pipeline metrics: {str(e)}"}


def query_station_metrics_via_pillar(connectivity, station_name: str) -> Dict[str, Any]:
    """Query metrics from a specific station via ConnectivityPillar."""
    try:
        response = connectivity.route_to_station(station_name, "metrics", {"command": "metrics"})
        return response if response else {"status": "no_metrics"}
    except Exception as e:
        return {"error": str(e)}
