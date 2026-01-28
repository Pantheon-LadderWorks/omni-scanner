"""
Node.js / JavaScript / TypeScript Deep Scanner
Analyzes package.json for Federation-wide dependency tracking
"""
from pathlib import Path
import json
from typing import Dict, List, Any


def scan(target: Path) -> dict:
    """
    Deep analysis of Node.js package.json files.
    
    Args:
        target: Path to scan (file or directory)
        
    Returns:
        dict with package metadata, dependencies, scripts, and Federation markers
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "node_scanner",
            "version": "1.0.0"
        },
        "summary": {
            "total_deps": 0,
            "total_dev_deps": 0,
            "total_peer_deps": 0,
            "scripts_count": 0,
            "federation_markers": []
        }
    }
    
    # Find package.json
    pkg_json = target / "package.json" if target.is_dir() else target
    
    if not pkg_json.exists() or pkg_json.name != "package.json":
        return results
    
    try:
        with open(pkg_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract core metadata
        package_info = {
            "path": str(pkg_json),
            "name": data.get("name", "unnamed"),
            "version": data.get("version", "0.0.0"),
            "description": data.get("description", ""),
            "type": data.get("type", "commonjs"),
            "private": data.get("private", False)
        }
        
        # Extract dependencies
        dependencies = data.get("dependencies", {})
        dev_dependencies = data.get("devDependencies", {})
        peer_dependencies = data.get("peerDependencies", {})
        
        package_info["dependencies"] = {
            "production": list(dependencies.keys()),
            "development": list(dev_dependencies.keys()),
            "peer": list(peer_dependencies.keys())
        }
        
        # Extract scripts
        scripts = data.get("scripts", {})
        package_info["scripts"] = list(scripts.keys())
        
        # Extract entry points
        package_info["entry_points"] = {
            "main": data.get("main"),
            "module": data.get("module"),
            "types": data.get("types") or data.get("typings"),
            "bin": data.get("bin")
        }
        
        # Detect Federation markers
        federation_markers = []
        
        # Check for SERAPHINA/Federation keywords
        keywords = data.get("keywords", [])
        if any(k.lower() in ["seraphina", "federation", "council", "agent"] for k in keywords):
            federation_markers.append("federation_keywords")
        
        # Check for MCP dependencies
        if any("mcp" in dep.lower() for dep in dependencies.keys()):
            federation_markers.append("mcp_dependency")
        
        # Check for Next.js (common in Federation UI projects)
        if "next" in dependencies or "next" in dev_dependencies:
            federation_markers.append("nextjs_project")
        
        # Check for React
        if "react" in dependencies:
            federation_markers.append("react_project")
        
        # Check for TypeScript
        if "typescript" in dev_dependencies or package_info["entry_points"].get("types"):
            federation_markers.append("typescript_enabled")
        
        package_info["federation_markers"] = federation_markers
        
        # Update summary
        results["summary"]["total_deps"] = len(dependencies)
        results["summary"]["total_dev_deps"] = len(dev_dependencies)
        results["summary"]["total_peer_deps"] = len(peer_dependencies)
        results["summary"]["scripts_count"] = len(scripts)
        results["summary"]["federation_markers"] = federation_markers
        
        # Add to items
        results["items"].append(package_info)
        results["count"] = 1
        
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        results["metadata"]["error"] = f"Failed to parse package.json: {str(e)}"
    
    return results


def extract_deep_dependencies(target: Path) -> Dict[str, Any]:
    """
    Extract flattened dependency tree (requires npm ls or yarn why).
    
    Note: This is a placeholder for future deep analysis.
    Currently returns basic dependency info.
    """
    result = scan(target)
    
    if result["count"] == 0:
        return {"dependencies": [], "dev_dependencies": []}
    
    pkg_info = result["items"][0]
    return {
        "dependencies": pkg_info["dependencies"]["production"],
        "dev_dependencies": pkg_info["dependencies"]["development"],
        "peer_dependencies": pkg_info["dependencies"]["peer"]
    }
