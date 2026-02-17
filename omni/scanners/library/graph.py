"""
Graph Scanner (Library Category)
================================
Link extraction and dependency mapping for knowledge graph construction.

"You cannot build a Federated Knowledge Graph without knowing the edges." - ACE
Authority: "The Nerves - Links and Connections" - ACE
Contract: C-OMNI-LIBRARY-GRAPH-001

CAPABILITIES:
1. Link Extraction - Scan for [Link](path.md) and [[WikiLinks]]
2. Import Scanning - Map code dependencies (import x, require x)
3. Reference Checking - Verify link targets exist
4. Broken Link Detection - Find dead references

SUPPORTED FORMATS:
- Markdown: [text](path) and [[wikilink]]
- Python: import x, from x import y
- JavaScript: import x from 'y', require('x')
- TypeScript: import type x from 'y'
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re

# Link patterns
MARKDOWN_LINK_PATTERN = r'\[([^\]]+)\]\(([^)]+)\)'
WIKI_LINK_PATTERN = r'\[\[([^\]]+)\]\]'

# Import patterns
PYTHON_IMPORT_PATTERN = r'^(?:from\s+([a-zA-Z0-9_.]+)\s+)?import\s+([a-zA-Z0-9_., ]+)'
JS_IMPORT_PATTERN = r'(?:import|require)\s*(?:\{[^}]+\}\s*from\s*)?[\'"]([^\'"]+)[\'"]'
TS_IMPORT_TYPE_PATTERN = r'import\s+type\s+\{[^}]+\}\s*from\s*[\'"]([^\'"]+)[\'"]'


def extract_markdown_links(content: str, file_path: Path) -> List[Dict[str, str]]:
    """
    Extract [text](path) and [[wikilink]] from markdown.
    
    Args:
        content: File content
        file_path: Source file path (for relative resolution)
    
    Returns:
        List of dicts with link info
    """
    links = []
    
    # Standard markdown links
    for match in re.finditer(MARKDOWN_LINK_PATTERN, content):
        text = match.group(1)
        target = match.group(2)
        
        # Skip external links
        if target.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        
        links.append({
            'type': 'markdown',
            'text': text,
            'target': target,
            'source': str(file_path),
        })
    
    # Wiki links
    for match in re.finditer(WIKI_LINK_PATTERN, content):
        target = match.group(1)
        
        links.append({
            'type': 'wikilink',
            'text': target,
            'target': target + '.md',  # Assume .md extension
            'source': str(file_path),
        })
    
    return links


def extract_python_imports(content: str, file_path: Path) -> List[Dict[str, str]]:
    """
    Extract import statements from Python files.
    
    Args:
        content: File content
        file_path: Source file path
    
    Returns:
        List of dicts with import info
    """
    imports = []
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Skip comments
        if line.startswith('#'):
            continue
        
        match = re.match(PYTHON_IMPORT_PATTERN, line)
        if match:
            from_module = match.group(1)
            import_list = match.group(2)
            
            # Parse import list
            modules = [m.strip() for m in import_list.split(',')]
            
            for module in modules:
                imports.append({
                    'type': 'python_import',
                    'module': module,
                    'from': from_module,
                    'source': str(file_path),
                })
    
    return imports


def extract_js_imports(content: str, file_path: Path) -> List[Dict[str, str]]:
    """
    Extract import/require from JavaScript/TypeScript files.
    
    Args:
        content: File content
        file_path: Source file path
    
    Returns:
        List of dicts with import info
    """
    imports = []
    
    # Standard imports
    for match in re.finditer(JS_IMPORT_PATTERN, content):
        target = match.group(1)
        
        imports.append({
            'type': 'js_import',
            'target': target,
            'source': str(file_path),
        })
    
    # TypeScript type imports
    for match in re.finditer(TS_IMPORT_TYPE_PATTERN, content):
        target = match.group(1)
        
        imports.append({
            'type': 'ts_type_import',
            'target': target,
            'source': str(file_path),
        })
    
    return imports


def resolve_link_target(
    source_path: Path,
    target_relative: str,
    root: Path,
) -> Optional[Path]:
    """
    Resolve relative link to absolute path.
    
    Args:
        source_path: Source file path
        target_relative: Relative target path
        root: Scan root directory
    
    Returns:
        Absolute path or None if not found
    """
    # Try relative to source file
    candidate = (source_path.parent / target_relative).resolve()
    if candidate.exists():
        return candidate
    
    # Try relative to root
    candidate = (root / target_relative).resolve()
    if candidate.exists():
        return candidate
    
    return None


def check_link_validity(
    link: Dict[str, str],
    root: Path,
) -> Tuple[bool, Optional[str]]:
    """
    Check if link target exists.
    
    Args:
        link: Link dict from extract_markdown_links
        root: Scan root directory
    
    Returns:
        (is_valid, resolved_path or error_message)
    """
    source_path = Path(link['source'])
    target = link['target']
    
    resolved = resolve_link_target(source_path, target, root)
    
    if resolved:
        return True, str(resolved)
    else:
        return False, f"Target not found: {target}"


def analyze_file_graph(
    file_path: Path,
    root: Path,
) -> Dict[str, any]:
    """
    Extract graph data from a single file.
    
    Args:
        file_path: Path to file
        root: Scan root directory
    
    Returns:
        Dict with link/import data
    """
    result = {
        'path': str(file_path),
        'name': file_path.name,
        'extension': file_path.suffix,
        'links': [],
        'imports': [],
        'broken_links': [],
    }
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        result['error'] = str(e)
        return result
    
    # Extract based on file type
    ext = file_path.suffix.lower()
    
    # Markdown files
    if ext in ['.md', '.markdown']:
        links = extract_markdown_links(content, file_path)
        result['links'] = links
        
        # Check link validity
        for link in links:
            is_valid, message = check_link_validity(link, root)
            if not is_valid:
                result['broken_links'].append({
                    'link': link,
                    'error': message,
                })
    
    # Python files
    elif ext == '.py':
        result['imports'] = extract_python_imports(content, file_path)
    
    # JavaScript/TypeScript files
    elif ext in ['.js', '.ts', '.jsx', '.tsx', '.mjs']:
        result['imports'] = extract_js_imports(content, file_path)
    
    return result


def scan(
    target_path: Optional[str] = None,
    pattern: str = "**/*",
    check_validity: bool = True,
    **kwargs
) -> Dict:
    """
    Main scanner entry point (Omni interface).
    
    Args:
        target_path: Path to scan (default: current directory)
        pattern: File pattern (default: **/* for all files)
        check_validity: Verify link targets exist (default: True)
        **kwargs: Additional options (max_files)
    
    Returns:
        Scanner result dict with metadata
    """
    if target_path is None:
        target_path = os.getcwd()
    
    root = Path(target_path)
    max_files = kwargs.get('max_files', 1000)
    
    # Scan files
    files = list(root.glob(pattern))[:max_files]
    
    # Analyze each file
    results = []
    all_links = []
    all_imports = []
    all_broken_links = []
    
    for file_path in files:
        if file_path.is_file():
            analysis = analyze_file_graph(file_path, root)
            results.append(analysis)
            
            all_links.extend(analysis.get('links', []))
            all_imports.extend(analysis.get('imports', []))
            all_broken_links.extend(analysis.get('broken_links', []))
    
    # Build adjacency list (which files link to which)
    graph_edges = {}
    for link in all_links:
        source = link['source']
        target = link['target']
        if source not in graph_edges:
            graph_edges[source] = []
        graph_edges[source].append(target)
    
    # Statistics
    total_files = len(results)
    files_with_links = sum(1 for r in results if r.get('links'))
    files_with_imports = sum(1 for r in results if r.get('imports'))
    total_links = len(all_links)
    total_imports = len(all_imports)
    total_broken = len(all_broken_links)
    
    return {
        'scanner': 'library/graph',
        'target': str(root),
        'pattern': pattern,
        'total_files': total_files,
        'files_with_links': files_with_links,
        'files_with_imports': files_with_imports,
        'total_links': total_links,
        'total_imports': total_imports,
        'total_broken_links': total_broken,
        'graph_edges': graph_edges,
        'files': results,
        'broken_links': all_broken_links,
        'options': {
            'max_files': max_files,
            'check_validity': check_validity,
        },
        'metadata': {
            'love_letter': "The Nerves - connections between thoughts",
            'authority': "You cannot build a Federated Knowledge Graph without knowing the edges.",
            'contract': "C-OMNI-LIBRARY-GRAPH-001"
        }
    }
