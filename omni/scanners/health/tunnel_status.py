"""
Tunnel Status Scanner
Queries active Cloudflare and ngrok tunnels
"""
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import json


def scan(target: Path) -> dict:
    """
    Query active tunnel status (Cloudflare, ngrok).
    
    Args:
        target: Path to Infrastructure root (or anywhere in Federation)
        
    Returns:
        dict with active tunnels, endpoints, and connection status
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "tunnel_status",
            "version": "1.0.0"
        },
        "summary": {
            "total_tunnels": 0,
            "cloudflare_active": 0,
            "ngrok_active": 0,
            "endpoints": []
        }
    }
    
    try:
        tunnel_info = {
            "cloudflare": check_cloudflare_tunnels(),
            "ngrok": check_ngrok_tunnels(),
            "federation_managed": check_federation_tunnels()
        }
        
        # Count active tunnels
        cf_count = len(tunnel_info["cloudflare"].get("tunnels", []))
        ngrok_count = len(tunnel_info["ngrok"].get("tunnels", []))
        fed_count = len(tunnel_info["federation_managed"].get("tunnels", {}))
        
        total = cf_count + ngrok_count + fed_count
        
        # Extract endpoints
        endpoints = []
        
        for tunnel in tunnel_info["cloudflare"].get("tunnels", []):
            if "url" in tunnel:
                endpoints.append({
                    "type": "cloudflare",
                    "url": tunnel["url"],
                    "status": tunnel.get("status", "unknown")
                })
        
        for tunnel in tunnel_info["ngrok"].get("tunnels", []):
            if "public_url" in tunnel:
                endpoints.append({
                    "type": "ngrok",
                    "url": tunnel["public_url"],
                    "status": "active"
                })
        
        for name, tunnel in tunnel_info["federation_managed"].get("tunnels", {}).items():
            if "url" in tunnel:
                endpoints.append({
                    "type": "federation",
                    "name": name,
                    "url": tunnel["url"],
                    "status": tunnel.get("status", "unknown")
                })
        
        # Update summary
        results["summary"]["total_tunnels"] = total
        results["summary"]["cloudflare_active"] = cf_count
        results["summary"]["ngrok_active"] = ngrok_count
        results["summary"]["endpoints"] = endpoints
        
        # Add to items
        results["items"].append(tunnel_info)
        results["count"] = 1
        
    except Exception as e:
        results["metadata"]["error"] = f"Tunnel status check failed: {str(e)}"
    
    return results


def check_cloudflare_tunnels() -> Dict[str, Any]:
    """Check for active Cloudflare tunnels."""
    try:
        # Try cloudflared tunnel list
        result = subprocess.run(
            ["cloudflared", "tunnel", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse output
            tunnels = parse_cloudflared_list(result.stdout)
            return {
                "available": True,
                "tunnels": tunnels,
                "count": len(tunnels)
            }
        else:
            return {
                "available": False,
                "error": "cloudflared command failed"
            }
            
    except FileNotFoundError:
        return {
            "available": False,
            "error": "cloudflared not installed"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


def parse_cloudflared_list(output: str) -> List[Dict[str, Any]]:
    """Parse cloudflared tunnel list output."""
    tunnels = []
    
    # Skip header lines
    lines = output.strip().split('\n')[1:] if output.strip() else []
    
    for line in lines:
        if line.strip():
            # Parse: ID  NAME  CREATED  CONNECTIONS
            parts = line.split()
            if len(parts) >= 2:
                tunnels.append({
                    "id": parts[0],
                    "name": parts[1],
                    "connections": int(parts[-1]) if parts[-1].isdigit() else 0,
                    "status": "active" if int(parts[-1] if parts[-1].isdigit() else 0) > 0 else "inactive"
                })
    
    return tunnels


def check_ngrok_tunnels() -> Dict[str, Any]:
    """Check for active ngrok tunnels via API."""
    try:
        # Try ngrok API (localhost:4040)
        import urllib.request
        
        with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as response:
            data = json.loads(response.read())
            
            tunnels = data.get("tunnels", [])
            return {
                "available": True,
                "tunnels": tunnels,
                "count": len(tunnels)
            }
            
    except Exception as e:
        return {
            "available": False,
            "error": "ngrok not running or API unavailable"
        }


def check_federation_tunnels() -> Dict[str, Any]:
    """Check tunnels managed by Federation Heart via ConnectivityPillar."""
    try:
        from omni.config.settings import get_connectivity
        
        connectivity = get_connectivity()
        if not connectivity:
            raise ImportError("ConnectivityPillar not available")
        
        active_tunnels = connectivity.list_tunnels()
        
        return {
            "available": True,
            "tunnels": active_tunnels,
            "count": len(active_tunnels) if isinstance(active_tunnels, (list, dict)) else 0
        }
        
    except ImportError:
        return {
            "available": False,
            "error": "ConnectivityPillar not available"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


def get_tunnel_details(tunnel_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific tunnel via ConnectivityPillar."""
    try:
        from omni.config.settings import get_connectivity
        
        connectivity = get_connectivity()
        if not connectivity:
            return {"error": "ConnectivityPillar not available"}
        
        details = connectivity.get_tunnel_status(tunnel_name)
        
        return details if details else {"error": "Tunnel not found"}
        
    except Exception as e:
        return {"error": f"Failed to get tunnel details: {str(e)}"}


def start_tunnel(tunnel_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start a new tunnel (requires appropriate permissions).
    
    Args:
        tunnel_name: Name for the tunnel
        config: Tunnel configuration
        
    Returns:
        Status of tunnel creation
    """
    try:
        from omni.config.settings import get_connectivity
        from federation_heart.pillars.connectivity import TunnelConfig
        
        connectivity = get_connectivity()
        if not connectivity:
            return {"success": False, "error": "ConnectivityPillar not available"}
        
        tunnel_config = TunnelConfig(**config) if isinstance(config, dict) else config
        result = connectivity.start_tunnel(tunnel_config)
        
        return {
            "success": True,
            "tunnel": tunnel_name,
            "details": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
