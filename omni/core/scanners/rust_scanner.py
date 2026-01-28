"""
Rust Crate Deep Scanner
Analyzes Cargo.toml for Federation-wide Rust dependency tracking
"""
from pathlib import Path
from typing import Dict, List, Any


def scan(target: Path) -> dict:
    """
    Deep analysis of Rust Cargo.toml files.
    
    Args:
        target: Path to scan (file or directory)
        
    Returns:
        dict with crate metadata, dependencies, features, and Federation markers
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "rust_scanner",
            "version": "1.0.0"
        },
        "summary": {
            "total_deps": 0,
            "total_dev_deps": 0,
            "total_build_deps": 0,
            "workspace_members": 0,
            "federation_markers": []
        }
    }
    
    # Find Cargo.toml
    cargo_toml = target / "Cargo.toml" if target.is_dir() else target
    
    if not cargo_toml.exists() or cargo_toml.name != "Cargo.toml":
        return results
    
    try:
        # Parse TOML manually (avoid toml dependency for now)
        with open(cargo_toml, 'r', encoding='utf-8') as f:
            content = f.read()
        
        crate_info = {
            "path": str(cargo_toml),
            "name": extract_toml_value(content, "name"),
            "version": extract_toml_value(content, "version"),
            "edition": extract_toml_value(content, "edition"),
            "description": extract_toml_value(content, "description")
        }
        
        # Extract dependencies
        dependencies = extract_toml_section(content, "[dependencies]")
        dev_dependencies = extract_toml_section(content, "[dev-dependencies]")
        build_dependencies = extract_toml_section(content, "[build-dependencies]")
        
        crate_info["dependencies"] = {
            "production": dependencies,
            "development": dev_dependencies,
            "build": build_dependencies
        }
        
        # Extract features
        features = extract_toml_section(content, "[features]")
        crate_info["features"] = features
        
        # Check for workspace
        workspace_members = extract_toml_array(content, "members", section="[workspace]")
        crate_info["workspace"] = {
            "is_workspace": bool(workspace_members),
            "members": workspace_members
        }
        
        # Detect Federation markers
        federation_markers = []
        
        # Check for CodeCraft native VM
        if "codecraft" in crate_info.get("name", "").lower():
            federation_markers.append("codecraft_vm")
        
        # Check for quantum dependencies (Q# interop)
        if any("quantum" in dep.lower() for dep in dependencies):
            federation_markers.append("quantum_enabled")
        
        # Check for MCP features
        if any("mcp" in dep.lower() for dep in dependencies):
            federation_markers.append("mcp_integration")
        
        # Check for async runtime (tokio/async-std)
        if "tokio" in dependencies or "async-std" in dependencies:
            federation_markers.append("async_runtime")
        
        # Check for WASM target
        if "wasm" in content.lower() or "web-sys" in dependencies:
            federation_markers.append("wasm_target")
        
        crate_info["federation_markers"] = federation_markers
        
        # Update summary
        results["summary"]["total_deps"] = len(dependencies)
        results["summary"]["total_dev_deps"] = len(dev_dependencies)
        results["summary"]["total_build_deps"] = len(build_dependencies)
        results["summary"]["workspace_members"] = len(workspace_members)
        results["summary"]["federation_markers"] = federation_markers
        
        # Add to items
        results["items"].append(crate_info)
        results["count"] = 1
        
    except (FileNotFoundError, PermissionError) as e:
        results["metadata"]["error"] = f"Failed to parse Cargo.toml: {str(e)}"
    
    return results


def extract_toml_value(content: str, key: str) -> str:
    """Extract a simple TOML key = "value" pair."""
    import re
    pattern = rf'^{key}\s*=\s*"([^"]*)"'
    match = re.search(pattern, content, re.MULTILINE)
    return match.group(1) if match else ""


def extract_toml_section(content: str, section_header: str) -> List[str]:
    """Extract dependency names from a TOML section."""
    import re
    
    # Find section
    section_start = content.find(section_header)
    if section_start == -1:
        return []
    
    # Find next section or end of file
    next_section = content.find("\n[", section_start + len(section_header))
    section_content = content[section_start:next_section] if next_section != -1 else content[section_start:]
    
    # Extract dependency names (key = ...)
    deps = []
    for line in section_content.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            dep_name = line.split('=')[0].strip()
            if dep_name and dep_name != section_header.strip('[]'):
                deps.append(dep_name)
    
    return deps


def extract_toml_array(content: str, key: str, section: str = "") -> List[str]:
    """Extract a TOML array value."""
    import re
    
    # Focus on section if specified
    search_content = content
    if section:
        section_start = content.find(section)
        if section_start != -1:
            next_section = content.find("\n[", section_start + len(section))
            search_content = content[section_start:next_section] if next_section != -1 else content[section_start:]
    
    # Find array: key = ["val1", "val2"]
    pattern = rf'{key}\s*=\s*\[(.*?)\]'
    match = re.search(pattern, search_content, re.DOTALL)
    
    if not match:
        return []
    
    array_content = match.group(1)
    items = re.findall(r'"([^"]*)"', array_content)
    return items
