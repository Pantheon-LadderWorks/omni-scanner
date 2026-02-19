"""
Text Search Scanner - High-Performance Literal Search
=====================================================

Simple, fast literal string search. optimized for "Find in Files" use cases.
Unlike pattern_search.py (regex), this uses direct string matching.

Contract: C-OMNI-SEARCH-TEXT-001
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import mimetypes
from omni.lib.files import walk_project

def search_text(
    target: str,
    query: str,
    case_sensitive: bool = False,
    max_results: int = 1000,
    context_lines: int = 1
) -> Dict[str, Any]:
    """
    Search for literal string across files.
    """
    target_path = Path(target)
    
    matches = []
    files_scanned = 0
    files_matched = 0
    truncated = False
    
    if not case_sensitive:
        query = query.lower()
        
    for file_path in walk_project(target_path):
        # Skip binary files
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and not mime_type.startswith('text'):
            continue
            
        files_scanned += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            file_has_match = False
            
            for line_num, line_text in enumerate(lines, start=1):
                # Search logic
                if case_sensitive:
                    found = query in line_text
                else:
                    found = query in line_text.lower()
                    
                if found:
                    file_has_match = True
                    
                    # Get context
                    context_before = [
                        lines[i].rstrip()
                        for i in range(max(0, line_num - context_lines - 1), line_num - 1)
                    ]
                    context_after = [
                        lines[i].rstrip()
                        for i in range(line_num, min(len(lines), line_num + context_lines))
                    ]
                    
                    matches.append({
                        "file": str(file_path),
                        "line_num": line_num,
                        "line_text": line_text.rstrip(),
                        "context_before": context_before,
                        "context_after": context_after
                    })
                    
                    if len(matches) >= max_results:
                        truncated = True
                        break
            
            if file_has_match:
                files_matched += 1
                
            if truncated:
                break
                
        except Exception:
            continue
            
    return {
        "success": True,
        "scanner": "search/text_search",
        "target": str(target_path),
        "results": {
            "matches": matches,
            "stats": {
                "total_matches": len(matches),
                "files_matched": files_matched,
                "files_scanned": files_scanned,
                "query": query,
                "truncated": truncated
            }
        }
    }
