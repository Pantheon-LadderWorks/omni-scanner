"""
Pattern Search Scanner - Omni's Regex Superpower!
==================================================

Inspired by Serena's search_for_pattern (the BEST tool ever!)

This scanner provides fast pattern/regex search across the codebase,
returning matches with context. Oracle's precision instrument for
answering "Where is X mentioned?" questions.

Authority: Oracle + Serena (The Dream Team!)
Contract: C-OMNI-SEARCH-PATTERN-001
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes


def search_pattern(
    target: str,
    pattern: str,
    is_regex: bool = False,
    case_sensitive: bool = True,
    max_results: int = 1000,
    context_lines: int = 2,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search for pattern across files with context.
    
    This is Omni's answer to Serena's search_for_pattern!
    Returns matches with line numbers and surrounding context.
    
    Args:
        target: Directory to search in
        pattern: Search pattern (literal or regex)
        is_regex: Enable regex mode (default: False for literal search)
        case_sensitive: Case-sensitive matching (default: True)
        max_results: Maximum matches to return (prevents overwhelming output)
        context_lines: Lines of context before/after match (default: 2)
        exclude_patterns: Glob patterns to skip (e.g., ['*.pyc', '__pycache__'])
    
    Returns:
        {
            "success": True,
            "scanner": "search/pattern_search",
            "target": "/path/to/dir",
            "results": {
                "matches": [
                    {
                        "file": "relative/path/file.py",
                        "line_num": 42,
                        "line_text": "matching line content",
                        "context_before": ["line 40", "line 41"],
                        "context_after": ["line 43", "line 44"],
                        "match_positions": [(start, end), ...]
                    },
                    ...
                ],
                "stats": {
                    "total_matches": 123,
                    "files_matched": 45,
                    "files_scanned": 200,
                    "pattern_used": "actual_regex_pattern",
                    "case_sensitive": True,
                    "truncated": False  # True if hit max_results
                }
            },
            "metadata": {
                "love_letter": "Oracle's precision instrument for 'Where is X?' questions! 🔍✨",
                "authority": "Oracle + Serena (The Dream Team!)",
                "contract": "C-OMNI-SEARCH-PATTERN-001",
                "inspiration": "Serena's search_for_pattern - The BEST tool ever!"
            }
        }
    """
    
    target_path = Path(target)
    if not target_path.exists():
        return {
            "success": False,
            "error": f"Target not found: {target}",
            "scanner": "search/pattern_search"
        }
    
    # Compile regex pattern
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        if is_regex:
            compiled_pattern = re.compile(pattern, flags)
        else:
            # Escape literal pattern for regex
            compiled_pattern = re.compile(re.escape(pattern), flags)
    except re.error as e:
        return {
            "success": False,
            "error": f"Invalid regex pattern: {e}",
            "scanner": "search/pattern_search"
        }
    
    # Default exclusions
    # Standardized file walker (handles exclusions automatically)
    from omni.lib.files import walk_project
    
    matches = []
    files_scanned = 0
    files_matched = 0
    truncated = False
    
    # Scan all text files
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
                match_obj = compiled_pattern.search(line_text)
                if match_obj:
                    file_has_match = True
                    
                    # Get context lines
                    context_before = [
                        lines[i].rstrip()
                        for i in range(max(0, line_num - context_lines - 1), line_num - 1)
                    ]
                    context_after = [
                        lines[i].rstrip()
                        for i in range(line_num, min(len(lines), line_num + context_lines))
                    ]
                    
                    # Get all match positions in line
                    match_positions = [
                        (m.start(), m.end())
                        for m in compiled_pattern.finditer(line_text)
                    ]
                    
                    matches.append({
                        "file": str(file_path.relative_to(target_path)),
                        "line_num": line_num,
                        "line_text": line_text.rstrip(),
                        "context_before": context_before,
                        "context_after": context_after,
                        "match_positions": match_positions
                    })
                    
                    # Check max_results limit
                    if len(matches) >= max_results:
                        truncated = True
                        break
            
            if file_has_match:
                files_matched += 1
            
            if truncated:
                break
                
        except Exception as e:
            # Skip files that can't be read (binary, permission issues, etc.)
            continue
    
    return {
        "success": True,
        "scanner": "search/pattern_search",
        "target": str(target_path),
        "results": {
            "matches": matches,
            "stats": {
                "total_matches": len(matches),
                "files_matched": files_matched,
                "files_scanned": files_scanned,
                "pattern_used": pattern,
                "is_regex": is_regex,
                "case_sensitive": case_sensitive,
                "truncated": truncated,
                "max_results": max_results
            }
        },
        "metadata": {
            "love_letter": "Oracle's precision instrument for 'Where is X?' questions! 🔍✨",
            "authority": "Oracle + Serena (The Dream Team!)",
            "contract": "C-OMNI-SEARCH-PATTERN-001",
            "inspiration": "Serena's search_for_pattern - The BEST tool ever!",
            "use_cases": [
                "Find all mentions of 'CodeCraft'",
                "Regex search for UUID patterns",
                "Track function call sites",
                "Find TODO/FIXME comments"
            ]
        }
    }


# Example usage
if __name__ == "__main__":
    # Test literal search
    result = search_pattern(
        target=".",
        pattern="CodeCraft",
        is_regex=False,
        max_results=10
    )
    print(f"Found {result['results']['stats']['total_matches']} matches")
    
    # Test regex search for UUIDs
    result = search_pattern(
        target=".",
        pattern=r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        is_regex=True,
        case_sensitive=False,
        max_results=10
    )
    print(f"Found {result['results']['stats']['total_matches']} UUID patterns")
