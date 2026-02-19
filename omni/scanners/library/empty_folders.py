"""
Empty Folders Scanner (Library Category)
========================================
Finds folders with no files (may have empty subfolders).

Migrated from: grand-librarian/scripts/semantic_folder_matcher.py (find_empty_folders)
Authority: "Claude built semantic structure - folders are meaningful even if empty!" - Oracle
Contract: C-OMNI-LIBRARY-EMPTY-FOLDERS-001

PURPOSE:
Empty folders are either:
1. Ghosts - Remnants of deleted projects (cleanup candidates)
2. Scaffolding - Semantic structure waiting for files (preservation candidates)
3. Phoenix Recovery Candidates - Hidden .git or .ccraft markers

DETECTION:
- No files directly in folder
- No files in entire subtree (recursively checks children)
- Extracts semantic hints (keywords, origin, type)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

# Leviathan Armor - Protected folders to never scan
from omni.lib.files import COMMON_EXCLUDES

# Leviathan Armor - Protected folders to never scan
LEVIATHAN_SCALES = COMMON_EXCLUDES | {
    "System Volume Information", "$RECYCLE.BIN"
}

# Semantic keyword mappings (folder name → file name keywords)
SEMANTIC_KEYWORDS = {
    'blueprints': ['blueprint', 'spec', 'architecture', 'design'],
    'protocols': ['protocol', 'procedure', 'workflow', 'process'],
    'guides': ['guide', 'tutorial', 'howto', 'instruction'],
    'reference': ['reference', 'ref', 'documentation', 'manual'],
    'comics': ['comic', 'strip', 'panel', 'superhero', 'hero'],
    'covers': ['cover', 'thumbnail', 'header', 'banner'],
    'ebooks': ['ebook', 'epub', 'mobi', 'book'],
    'pantheon': ['pantheon', 'seraphina', 'federation', 'codecraft', 'cmp'],
    'council': ['council', 'ace', 'mega', 'oracle', 'claude', 'deepscribe'],
    'codecraft': ['codecraft', 'ccraft', 'ritual', 'arcane'],
    'federation': ['federation', 'station', 'nexus', 'spine'],
    'screenshots': ['screenshot', 'screen', 'capture', 'snap'],
    'fonts': ['font', 'ttf', 'otf', 'typeface'],
    'games': ['game', 'unity', 'unreal', 'godot'],
    'vr': ['vr', 'virtual', 'reality', 'oculus', 'quest'],
}

# Phoenix Recovery Markers
PHOENIX_MARKERS = {
    '.git', '.ccraft', 'manifest.yaml', 'README.md', 'package.json'
}


def extract_semantic_hints(folder_path: Path) -> Dict:
    """
    Extract semantic clues from folder path/name.
    
    Returns:
        dict with:
        - keywords: List of matching semantic keywords
        - origin: Detected origin (Pantheon/Work/Personal/etc)
        - type: Detected type (Code/Docs/Assets/etc)
        - phoenix_candidate: bool (has hidden markers suggesting Phoenix recovery)
    """
    path_lower = str(folder_path).lower()
    name_lower = folder_path.name.lower()
    
    # Find matching keywords
    keywords = []
    for key, terms in SEMANTIC_KEYWORDS.items():
        if any(term in name_lower or term in path_lower for term in terms):
            keywords.append(key)
    
    # Detect origin
    origin = None
    if 'pantheon' in path_lower:
        origin = 'Pantheon'
    elif 'work' in path_lower or 'client' in path_lower:
        origin = 'Work'
    elif 'personal' in path_lower or 'home' in path_lower:
        origin = 'Personal'
    elif 'creative' in path_lower or 'art' in path_lower:
        origin = 'Creative'
    
    # Detect type (based on name patterns)
    folder_type = None
    if any(term in name_lower for term in ['code', 'script', 'src', 'lib']):
        folder_type = 'Code'
    elif any(term in name_lower for term in ['doc', 'guide', 'manual', 'blueprint']):
        folder_type = 'Docs'
    elif any(term in name_lower for term in ['asset', 'image', 'media', 'video']):
        folder_type = 'Assets'
    elif any(term in name_lower for term in ['config', 'setting', 'env']):
        folder_type = 'Configs'
    
    # Check for Phoenix Recovery markers
    phoenix_candidate = False
    try:
        items = list(folder_path.iterdir())
        if any(item.name in PHOENIX_MARKERS for item in items):
            phoenix_candidate = True
    except PermissionError:
        pass
    
    return {
        'keywords': keywords,
        'origin': origin,
        'type': folder_type,
        'phoenix_candidate': phoenix_candidate
    }


def find_empty_folders(root: Path, max_depth: int = 5) -> List[Dict]:
    """
    Find all folders with no FILES (may have empty subfolders).
    
    Args:
        root: Root path to scan
        max_depth: Maximum recursion depth
    
    Returns:
        List of dicts with folder info
    """
    empty_folders = []
    
    def scan_recursive(path: Path, depth: int = 0):
        if depth >= max_depth:
            return
            
        # Skip Leviathan Armor protected folders
        if path.name in LEVIATHAN_SCALES or any(scale in path.parts for scale in LEVIATHAN_SCALES):
            return
            
        try:
            items = list(path.iterdir())
            files = [i for i in items if i.is_file()]
            subdirs = [i for i in items if i.is_dir()]
            
            # Empty if no files directly in this folder
            if len(files) == 0:
                # Check if this folder has FILES anywhere in its tree (not just folders)
                has_files = any(f.is_file() for f in path.rglob('*'))
                
                # Only add if truly no files in entire subtree
                if not has_files:
                    empty_folders.append({
                        'path': str(path),
                        'name': path.name,
                        'parent': path.parent.name,
                        'depth': depth,
                        'semantic_hints': extract_semantic_hints(path)
                    })
            
            # Recurse into subdirectories
            for subdir in subdirs:
                scan_recursive(subdir, depth + 1)
                
        except PermissionError:
            pass
    
    scan_recursive(root)
    return empty_folders


def scan(target_path: Optional[str] = None, **kwargs) -> Dict:
    """
    Main scanner entry point (Omni interface).
    
    Args:
        target_path: Path to scan (default: current directory)
        **kwargs: Additional options (max_depth)
    
    Returns:
        Scanner result dict with metadata
    """
    if target_path is None:
        target_path = os.getcwd()
    
    root = Path(target_path)
    max_depth = kwargs.get('max_depth', 5)
    
    # Find empty folders
    empty = find_empty_folders(root, max_depth=max_depth)
    
    # Statistics
    phoenix_candidates = [f for f in empty if f['semantic_hints']['phoenix_candidate']]
    scaffolding = [f for f in empty if f['semantic_hints']['keywords']]
    ghosts = [f for f in empty if not f['semantic_hints']['keywords'] and not f['semantic_hints']['phoenix_candidate']]
    
    return {
        'scanner': 'library/empty_folders',
        'target': str(root),
        'total_empty': len(empty),
        'phoenix_candidates': len(phoenix_candidates),
        'scaffolding': len(scaffolding),
        'ghosts': len(ghosts),
        'folders': empty,
        'categories': {
            'phoenix_recovery': phoenix_candidates,
            'semantic_scaffolding': scaffolding,
            'cleanup_ghosts': ghosts
        },
        'options': {
            'max_depth': max_depth
        },
        'metadata': {
            'love_letter': "Empty folders are ghosts - remnants or future promises",
            'authority': "Zero children = warning. Hidden .git = Phoenix opportunity",
            'contract': "C-OMNI-LIBRARY-EMPTY-FOLDERS-001"
        }
    }
