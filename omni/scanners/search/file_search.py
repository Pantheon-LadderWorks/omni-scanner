"""
File Search Scanner - "Go to File" Capability
=============================================

Finds files by name, supporting exact and fuzzy matching.
Useful for locating specific artifacts or components.

Contract: C-OMNI-SEARCH-FILE-001
"""

from pathlib import Path
from typing import Dict, Any, List
from omni.lib.files import walk_project

def search_files(
    target: str,
    name_pattern: str,
    fuzzy: bool = True,
    max_results: int = 100
) -> Dict[str, Any]:
    """
    Search for files by name.
    """
    target_path = Path(target)
    query = name_pattern.lower()
    
    matches = []
    files_scanned = 0
    truncated = False
    
    for file_path in walk_project(target_path):
        files_scanned += 1
        name = file_path.name.lower()
        
        found = False
        if fuzzy:
            if query in name:
                found = True
        else:
            if query == name:
                found = True
                
        if found:
            matches.append({
                "path": str(file_path),
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "extension": file_path.suffix
            })
            
        if len(matches) >= max_results:
            truncated = True
            break
            
    return {
        "success": True,
        "scanner": "search/file_search",
        "target": str(target_path),
        "results": {
            "matches": matches,
            "stats": {
                "total_matches": len(matches),
                "files_scanned": files_scanned,
                "query": name_pattern,
                "mode": "fuzzy" if fuzzy else "exact",
                "truncated": truncated
            }
        }
    }
