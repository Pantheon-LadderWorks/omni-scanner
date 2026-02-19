"""
Coupling Scanner (Architecture Category)
========================================
The Spaghett-O-Meter. Graphs the codebase to find circular dependencies and tangles.

" Architecture is about drawing lines. Coupling is about crossing them."

Authority:
    - C-HEART-ORCHESTRATION-001 (Loose Coupling)
    - C-OMNI-ARCHITECTURE-002 (Acyclic Dependencies)

Capabilities:
    - Builds a NetworkX graph of module imports
    - Detects Circular Dependencies (Cycles)
    - Measures "Tangle Factor" (Graph Density)
    - Identifies "God Modules" (High In-Degree/Out-Degree)

Usage:
    omni scan --scanners=architecture.coupling .
"""

import networkx as nx
from pathlib import Path
from typing import Dict, Any, List

from omni.config import settings
from omni.scanners.architecture.imports import extract_imports

def scan(target: Path, **options) -> Dict[str, Any]:
    """
    Scan for Architectural Coupling.
    """
    target = Path(target)
    
    # 1. Build the Graph
    G = nx.DiGraph()
    
    # Resolve root
    # If target is provided, use it. Otherwise fallback to settings.
    infra_root = target if target and target.name != "." else (settings.get_infrastructure_root() or target)
    infra_root = infra_root.resolve()
    
    # Walk and Graph
    files_scanned = 0
    
    skip_dirs = {
        "__pycache__", ".git", "node_modules", ".venv", "venv",
        "archive", ".tox", "build", "dist", ".eggs",
        "external-frameworks", "tests"
    }

    print(f"🕸️  Weaving Dependency Graph for {infra_root}...")

    # Map file paths to module names (approximate)
    # e.g. tools/omni/omni/core/system.py -> omni.core.system
    
    for py_file in infra_root.rglob("*.py"):
        if any(skip in py_file.parts for skip in skip_dirs):
            continue

        files_scanned += 1
        
        # Determine Source Module Name
        try:
            rel_path = py_file.relative_to(infra_root)
            # Naive module conversion: tools/omni/foo.py -> tools.omni.foo
            module_name = ".".join(rel_path.with_suffix("").parts)
        except ValueError:
            module_name = py_file.name

        G.add_node(module_name, type="file")
        
        # Extract Imports (Edges)
        imports = extract_imports(py_file)
        
        for imp in imports:
            target_module = imp["module"]
            # Filter standard library? (Hard without a list, but we focus on internal mostly)
            # For now, just add all edges.
            
            # Optimization: Only trace edges to known internal prefixes?
            # omni, federation_heart, stations, agents
            internal_prefixes = ("omni", "federation_heart", "stations", "agents", "tools")
            
            if target_module.startswith(internal_prefixes):
                G.add_edge(module_name, target_module)

    # 2. Analyze the Graph
    
    # Cycles
    try:
        cycles = list(nx.simple_cycles(G))
    except Exception:
        cycles = [] # Computationally expensive on large graphs, might switch to finding just report
        
    # Density
    density = nx.density(G)
    
    # Top Hubs (God Modules)
    degree_dict = dict(G.degree(G.nodes()))
    sorted_degree = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)
    top_hubs = [{"module": k, "degree": v} for k, v in sorted_degree[:5]]
    
    # Populate Items for Reporting
    items = []
    
    for cycle in cycles[:10]:
        items.append({
            "type": "cycle",
            "severity": "high",
            "description": f"Circular dependency: {' -> '.join(cycle)}",
            "cycle": cycle,
            "location": f"{cycle[0]} -> {cycle[1]}" if len(cycle)>1 else str(cycle)
        })

    for hub in top_hubs:
        items.append({
            "type": "god_module",
            "severity": "medium", 
            "description": f"High coupling: {hub['module']} (Degree: {hub['degree']})",
            "module": hub['module'],
            "degree": hub['degree'],
            "location": hub['module']
        })

    print(f"🕸️  Graph Built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    return {
        "scanner": "architecture.coupling",
        "metrics": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": density,
            "cycle_count": len(cycles)
        },
        "items": items,
        "cycles": cycles[:10], # Keep specific keys for specialized consumers
        "god_modules": top_hubs
    }
